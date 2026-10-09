"""Read-only English -> German coverage pilot (evaluation only).

Implements the reproducible, read-only procedure specified in
``docs/data-import/coverage-study.md``. It never writes to the database, never
changes the application, and never imports external data into the product. It
streams the Wiktextract JSONL artefacts and the FreeDict TEI source, selects a
deterministic sample, and reports coverage/quality metrics to a JSON file.

Contract (from the plan)::

    python -m scripts.import.pilot_coverage \
      --en data/raw/en/raw-wiktextract-data.jsonl.gz \
      --de data/raw/de/raw-wiktextract-data.jsonl.gz \
      --freedict data/raw/freedict/eng-deu.tei \
      --sample data/processed/pilot-sample.json \
      --report data/processed/pilot-coverage.json

If ``--sample`` already exists it is loaded and scored; pass
``--rebuild-sample`` to regenerate it. The sample file is written only when its
target does not already exist (or ``--rebuild-sample`` is given), so a previous
selection is never silently overwritten.

Language policy: a Wiktionary *page* may describe a word of any language. Every
record is classified by its own ``lang_code`` field, never by the artefact's
edition. English headwords require ``lang_code == "en"``; German enrichment
requires ``lang_code == "de"``.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.paths import ensure_paths

ensure_paths()

PROCEDURE_VERSION = "pilot-coverage/1.0"
SEED = 20261008
CORE_SIZE = 120
STRATIFIED_PER_CLASS = 10
CORE_POS = ("noun", "verb", "adj", "adv")
STRATIFIED_CLASSES = (
    "irregular_verb",
    "polysemy",
    "multi_de",
    "labels",
    "examples",
    "no_de",
)

URLS = {
    "en": "https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz",
    "de": "https://kaikki.org/dewiktionary/raw-wiktextract-data.jsonl.gz",
    "freedict": (
        "https://download.freedict.org/dictionaries/eng-deu/1.9-fd1/"
        "freedict-eng-deu-1.9-fd1.src.tar.xz"
    ),
}

GENDER_TAGS = {"masculine", "feminine", "neuter", "m", "f", "n"}

# Fields that have no faithful target in the proposed data model (readiness doc
# §4); counted for the field-fidelity metric, never silently dropped.
LOSSY_SENSE_FIELDS = ("senseid", "wikidata", "form_of", "alt_of")
LOSSY_FORM_FIELDS = ("ipa", "roman", "source")
LOSSY_RECORD_FIELDS = ("sounds",)


@dataclass
class Scan:
    """Counters for one streaming pass over a JSONL artefact."""

    lines: int = 0
    records: int = 0
    parse_errors: int = 0


def iter_records(
    path: Path, scan: Scan | None = None, max_lines: int | None = None
) -> Iterator[dict[str, Any]]:
    """Yield JSON objects from a JSONL file (``.gz`` or plain), streaming."""
    text_path = str(path)
    opener = gzip.open if text_path.endswith(".gz") else open
    with opener(text_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if scan is not None:
                scan.lines += 1
                if max_lines is not None and scan.lines > max_lines:
                    break
            text = line.strip()
            if not text:
                continue
            try:
                obj = json.loads(text)
            except json.JSONDecodeError:
                if scan is not None:
                    scan.parse_errors += 1
                continue
            if not isinstance(obj, dict):
                if scan is not None:
                    scan.parse_errors += 1
                continue
            if scan is not None:
                scan.records += 1
            yield obj


def record_key(rec: dict[str, Any]) -> str:
    """Stable identity tuple ``word \\t pos \\t etymology_number``."""
    return make_key(
        rec.get("word") or "",
        rec.get("pos") or "",
        str(rec.get("etymology_number") or "0"),
    )


def make_key(word: str, pos: str, etymology: str) -> str:
    return f"{word}\t{pos}\t{etymology}"


def split_key(key: str) -> tuple[str, str, str]:
    word, pos, etym = key.split("\t")
    return word, pos, etym


def key_to_entry(key: str, cls: str) -> dict[str, str]:
    word, pos, etym = split_key(key)
    return {"word": word, "pos": pos, "etymology_number": etym, "class": cls}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def headword_translations(rec: dict[str, Any]) -> list[dict[str, Any]]:
    return [t for t in _as_list(rec.get("translations")) if isinstance(t, dict)]


def sense_translations(rec: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for s in _as_list(rec.get("senses")):
        if isinstance(s, dict):
            out.extend(t for t in _as_list(s.get("translations")) if isinstance(t, dict))
    return out


def has_de_translation(rec: dict[str, Any]) -> bool:
    pool = headword_translations(rec) + sense_translations(rec)
    return any(t.get("code") == "de" for t in pool)


def has_sense_multi_de(rec: dict[str, Any]) -> bool:
    for s in _as_list(rec.get("senses")):
        if not isinstance(s, dict):
            continue
        count = sum(
            1
            for t in _as_list(s.get("translations"))
            if isinstance(t, dict) and t.get("code") == "de"
        )
        if count >= 2:
            return True
    return False


def is_irregular_verb(rec: dict[str, Any]) -> bool:
    if rec.get("pos") != "verb":
        return False
    for f in _as_list(rec.get("forms")):
        if not isinstance(f, dict):
            continue
        tags = set(_as_list(f.get("tags")))
        if "past" in tags or "participle" in tags:
            return True
    return False


def is_polysemous(rec: dict[str, Any]) -> bool:
    return len(_as_list(rec.get("senses"))) >= 3


def has_sense_labels(rec: dict[str, Any]) -> bool:
    return any(
        isinstance(s, dict) and _as_list(s.get("tags")) for s in _as_list(rec.get("senses"))
    )


def has_sense_examples(rec: dict[str, Any]) -> bool:
    return any(
        isinstance(s, dict) and _as_list(s.get("examples")) for s in _as_list(rec.get("senses"))
    )


def select_core(
    keys: list[str], size: int = CORE_SIZE, seed: int = SEED
) -> tuple[list[str], int, int, int]:
    """Alphabetically-spread deterministic stride over the sorted key list.

    Returns ``(selected, population, stride, offset)``. ``stride = max(1,
    population // size)``; the walk starts at ``seed % stride`` and takes every
    stride-th key until ``size`` keys are collected (or fewer if the population
    is smaller than ``size``).
    """
    ordered = sorted(keys)
    population = len(ordered)
    if population == 0:
        return [], 0, 1, 0
    stride = max(1, population // size)
    offset = seed % stride
    return ordered[offset::stride][:size], population, stride, offset


def build_sample(
    en_path: Path, max_lines: int | None = None
) -> tuple[dict[str, Any], Scan, dict[str, Any]]:
    """Stream the English artefact and build the deterministic sample."""
    core: set[str] = set()
    stratified: dict[str, set[str]] = {c: set() for c in STRATIFIED_CLASSES}
    scan = Scan()
    for rec in iter_records(en_path, scan, max_lines):
        if rec.get("lang_code") != "en":
            continue
        key = record_key(rec)
        if rec.get("pos") in CORE_POS:
            core.add(key)
        if is_irregular_verb(rec):
            stratified["irregular_verb"].add(key)
        if is_polysemous(rec):
            stratified["polysemy"].add(key)
        if has_sense_multi_de(rec):
            stratified["multi_de"].add(key)
        if has_sense_labels(rec):
            stratified["labels"].add(key)
        if has_sense_examples(rec):
            stratified["examples"].add(key)
        if not has_de_translation(rec):
            stratified["no_de"].add(key)

    selected_core, population, stride, offset = select_core(sorted(core))
    entries = [key_to_entry(k, "core") for k in selected_core]
    for cls in STRATIFIED_CLASSES:
        for key in sorted(stratified[cls])[:STRATIFIED_PER_CLASS]:
            entries.append(key_to_entry(key, cls))

    sample: dict[str, Any] = {
        "procedure_version": PROCEDURE_VERSION,
        "seed": SEED,
        "core_size": CORE_SIZE,
        "stratified_per_class": STRATIFIED_PER_CLASS,
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "core_population": population,
        "core_stride": stride,
        "core_offset": offset,
        "stratified_population": {c: len(stratified[c]) for c in STRATIFIED_CLASSES},
        "entries": entries,
    }
    return sample, scan, {
        "core_population": population,
        "core_stride": stride,
        "core_offset": offset,
        "stratified_population": {c: len(stratified[c]) for c in STRATIFIED_CLASSES},
    }


def german_equivalents(rec: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract German equivalents with their provenance level and sense index."""
    out: list[dict[str, Any]] = []
    for t in headword_translations(rec):
        if t.get("code") == "de":
            out.append(_translation(t, "headword", None))
    for i, s in enumerate(_as_list(rec.get("senses"))):
        if not isinstance(s, dict):
            continue
        idx = s.get("sense_index", i)
        for t in _as_list(s.get("translations")):
            if isinstance(t, dict) and t.get("code") == "de":
                out.append(_translation(t, "sense", idx))
    return out


def _translation(t: dict[str, Any], level: str, sense_index: Any) -> dict[str, Any]:
    return {
        "level": level,
        "sense_index": sense_index,
        "word": t.get("word"),
        "tags": _as_list(t.get("tags")),
        "note": t.get("note"),
        "sense": t.get("sense"),
        "english": t.get("english"),
        "roman": t.get("roman"),
        "lang": t.get("lang"),
    }


def analyze_entry(
    rec: dict[str, Any], de_index: dict[str, dict[str, Any]], errors: list[dict[str, Any]]
) -> dict[str, Any]:
    """Per-entry factual analysis used by the aggregate metrics."""
    word = rec.get("word") or ""
    pos = rec.get("pos") or ""
    senses = [s for s in _as_list(rec.get("senses")) if isinstance(s, dict)]
    forms = [f for f in _as_list(rec.get("forms")) if isinstance(f, dict)]
    de_eq = german_equivalents(rec)

    if not word or not pos:
        errors.append({"class": "invalid_record", "word": word, "detail": "missing word/pos"})

    de_words = [e for e in de_eq if e.get("word")]
    distinct_de = {str(e["word"]).casefold() for e in de_words}

    examples = [ex for s in senses for ex in _as_list(s.get("examples")) if isinstance(ex, dict)]
    examples_with_translation = sum(1 for ex in examples if ex.get("translation"))

    inflected_forms = [
        f for f in forms if f.get("form") and f.get("form") != "-" and f.get("form") != word
    ]
    gloss_texts = {_norm(g) for s in senses for g in _as_list(s.get("glosses")) if g}

    # Defect bookkeeping (never silently dropped).
    no_sense_de = bool(de_eq) and not any(e["level"] == "sense" for e in de_eq)
    if not de_eq:
        errors.append({"class": "no_german_translation", "word": word, "detail": pos})
    elif no_sense_de:
        errors.append(
            {
                "class": "sense_unmapped",
                "word": word,
                "detail": "German equivalents only at headword level",
            }
        )
    if any(e.get("note") and not e.get("word") for e in de_eq):
        errors.append({"class": "word_field_absent", "word": word, "detail": "note without word"})
    for e in de_eq:
        sense_text = e.get("sense")
        if sense_text and _norm(sense_text) not in gloss_texts:
            errors.append(
                {
                    "class": "sense_text_unmatched",
                    "word": word,
                    "detail": str(sense_text)[:80],
                }
            )
    for level in {e["level"] for e in de_eq}:
        words_here = [
            str(e["word"]).casefold()
            for e in de_eq
            if e["level"] == level and e.get("word")
        ]
        dupes = {w for w in words_here if words_here.count(w) > 1}
        for dup in dupes:
            errors.append({"class": "duplicate_translation", "word": word, "detail": dup})

    # German enrichment (de edition).
    matched = [de_index.get(w.casefold()) for w in {str(e["word"]) for e in de_words}]
    de_matches = [m for m in matched if m]
    en_gender = sum(1 for e in de_eq if set(e["tags"]) & GENDER_TAGS)
    de_gender = sum(
        1 for m in de_matches if any(t in GENDER_TAGS for t in _as_list(m.get("gender_tags")))
    )
    de_with_forms = sum(1 for m in de_matches if m.get("form_count", 0) > 0)
    de_with_gloss = sum(1 for m in de_matches if m.get("has_gloss"))

    return {
        "word": word,
        "pos": pos,
        "etymology_number": str(rec.get("etymology_number") or "0"),
        "lang_code": rec.get("lang_code"),
        "has_de": bool(de_eq),
        "de_equivalents": de_eq,
        "distinct_de": sorted(distinct_de),
        "senses_total": len(senses),
        "senses_with_any_translation": sum(1 for s in senses if _as_list(s.get("translations"))),
        "senses_with_de": sum(
            1
            for s in senses
            if any(
                isinstance(t, dict) and t.get("code") == "de"
                for t in _as_list(s.get("translations"))
            )
        ),
        "has_definition": any(_as_list(s.get("glosses")) for s in senses),
        "senses_with_tags": sum(1 for s in senses if _as_list(s.get("tags"))),
        "examples_total": len(examples),
        "examples_with_translation": examples_with_translation,
        "inflected_forms": len(inflected_forms),
        "de_words": len(de_words),
        "de_matched": len(de_matches),
        "en_gender_labels": en_gender,
        "de_gender_labels": de_gender,
        "de_with_forms": de_with_forms,
        "de_with_gloss": de_with_gloss,
    }


def _norm(text: Any) -> str:
    import unicodedata

    return unicodedata.normalize("NFC", str(text)).strip().casefold()


def build_de_index(
    de_path: Path, needed: set[str], scan: Scan, max_lines: int | None = None
) -> dict[str, dict[str, Any]]:
    """Index German records for the needed (casefolded) German lemmas."""
    index: dict[str, dict[str, Any]] = {}
    for rec in iter_records(de_path, scan, max_lines):
        if rec.get("lang_code") != "de":
            continue
        word = rec.get("word")
        if not word:
            continue
        norm = str(word).casefold()
        if norm not in needed or norm in index:
            continue
        senses = [s for s in _as_list(rec.get("senses")) if isinstance(s, dict)]
        index[norm] = {
            "word": word,
            "pos": rec.get("pos"),
            "gender_tags": [t for t in _as_list(rec.get("tags")) if t in GENDER_TAGS],
            "form_count": len([f for f in _as_list(rec.get("forms")) if isinstance(f, dict)]),
            "has_gloss": any(_as_list(s.get("glosses")) for s in senses),
        }
    return index


def parse_freedict_tei(
    path: Path, needed: set[str]
) -> tuple[dict[str, list[dict[str, Any]]], int]:
    """Stream the FreeDict TEI and index entries whose headword is needed."""
    import xml.etree.ElementTree as ET

    result: dict[str, list[dict[str, Any]]] = {}
    scanned = 0
    for _event, elem in ET.iterparse(str(path), events=("end",)):
        if _local(elem.tag) != "entry":
            continue
        scanned += 1
        orth = _first_desc(elem, "orth")
        head = (orth.text or "").strip() if orth is not None else ""
        if head.casefold() in needed:
            trans: list[dict[str, Any]] = []
            for cit in elem.iter():
                if _local(cit.tag) != "cit" or cit.attrib.get("type") != "trans":
                    continue
                for quote in cit.iter():
                    if _local(quote.tag) != "quote" or _xml_lang(quote) != "de":
                        continue
                    gen = number = None
                    for g in cit.iter():
                        name = _local(g.tag)
                        if name == "gen":
                            gen = "".join(g.itertext()).strip()
                        elif name == "number":
                            number = "".join(g.itertext()).strip()
                    trans.append(
                        {"text": "".join(quote.itertext()).strip(), "gen": gen, "number": number}
                    )
            result.setdefault(head.casefold(), []).extend(trans)
        elem.clear()
    return result, scanned


def _local(tag: Any) -> str:
    return str(tag).rsplit("}", 1)[-1]


def _first_desc(elem: Any, name: str) -> Any:
    for child in elem.iter():
        if _local(child.tag) == name:
            return child
    return None


def _xml_lang(elem: Any) -> str | None:
    for key, value in elem.attrib.items():
        if key.endswith("lang"):
            return value
    return None


def _metric(source: str, num: Any, den: Any, note: str = "") -> dict[str, Any]:
    if num is None or den is None:
        return {
            "source": source,
            "numerator": num,
            "denominator": den,
            "pct": None,
            "status": "PENDING",
            "limitations": note,
        }
    if den == 0:
        return {
            "source": source,
            "numerator": num,
            "denominator": den,
            "pct": None,
            "status": "N/A",
            "limitations": note or "denominator is zero",
        }
    return {
        "source": source,
        "numerator": num,
        "denominator": den,
        "pct": round(100.0 * num / den, 2),
        "status": "MEASURED",
        "limitations": note,
    }


def compute_metrics(analyses: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    entries = len(analyses)
    senses = sum(a["senses_total"] for a in analyses)
    de_eq_total = sum(len(a["de_equivalents"]) for a in analyses)
    examples = sum(a["examples_total"] for a in analyses)
    de_matched = sum(a["de_matched"] for a in analyses)
    return {
        "entries_scored": _metric("en", entries, entries),
        "german_translation_coverage": _metric(
            "en",
            sum(1 for a in analyses if a["has_de"]),
            entries,
            "entry has >=1 translation object with code == de (headword- or sense-level)",
        ),
        "entries_with_multiple_german_equivalents": _metric(
            "en",
            sum(1 for a in analyses if len(a["distinct_de"]) >= 2),
            entries,
            "distinct German surfaces per entry, casefolded",
        ),
        "definition_coverage": _metric(
            "en",
            sum(1 for a in analyses if a["has_definition"]),
            entries,
            "entry has >=1 sense with a non-empty glosses list",
        ),
        "sense_translation_association": _metric(
            "en",
            sum(a["senses_with_any_translation"] for a in analyses),
            senses,
            "of all senses, share carrying any sense-level translation",
        ),
        "sense_german_association": _metric(
            "en",
            sum(a["senses_with_de"] for a in analyses),
            senses,
            "of all senses, share carrying a sense-level German translation",
        ),
        "gender_label_coverage_en_translations": _metric(
            "en",
            sum(a["en_gender_labels"] for a in analyses),
            de_eq_total,
            "German equivalents carrying a gender tag in the English translation object",
        ),
        "german_enrichment_gender": _metric(
            "de",
            sum(a["de_gender_labels"] for a in analyses),
            de_matched,
            "matched de-edition records with a top-level gender tag",
        ),
        "inflection_coverage_en": _metric(
            "en",
            sum(1 for a in analyses if a["inflected_forms"] > 0),
            entries,
            "entry carries >=1 form that differs from the headword",
        ),
        "german_enrichment_forms": _metric(
            "de",
            sum(a["de_with_forms"] for a in analyses),
            de_matched,
            "matched de-edition records carrying >=1 form",
        ),
        "example_coverage": _metric(
            "en",
            sum(1 for a in analyses if a["examples_total"] > 0),
            entries,
            "entry has >=1 sense example",
        ),
        "example_translation_coverage": _metric(
            "en",
            sum(a["examples_with_translation"] for a in analyses),
            examples,
            "examples carrying a translation field",
        ),
        "sense_tag_coverage": _metric(
            "en",
            sum(a["senses_with_tags"] for a in analyses),
            senses,
            "senses carrying non-empty usage/grammar tags",
        ),
        "german_enrichment_matched": _metric(
            "de",
            de_matched,
            sum(a["de_words"] for a in analyses),
            "German equivalents found by exact casefold match in the de edition",
        ),
    }


def score_sample(
    sample: dict[str, Any],
    en_path: Path,
    de_path: Path | None,
    freedict_path: Path | None,
    *,
    max_lines: int | None = None,
    progress: bool = True,
) -> dict[str, Any]:
    key_classes: dict[str, set[str]] = {}
    for entry in sample.get("entries", []):
        key = make_key(entry["word"], entry["pos"], entry["etymology_number"])
        key_classes.setdefault(key, set()).add(entry["class"])

    errors: list[dict[str, Any]] = []
    captured: dict[str, dict[str, Any]] = {}
    en_scan = Scan()
    for rec in iter_records(en_path, en_scan, max_lines):
        if rec.get("lang_code") != "en":
            continue
        key = record_key(rec)
        if key in key_classes and key not in captured:
            captured[key] = rec

    missing = [k for k in key_classes if k not in captured]
    for key in missing:
        word, pos, _etym = split_key(key)
        errors.append({"class": "missing_record", "word": word, "detail": pos})

    # Pass over the German edition for the equivalents seen in the sample.
    needed_de: set[str] = set()
    for rec in captured.values():
        for e in german_equivalents(rec):
            if e.get("word"):
                needed_de.add(str(e["word"]).casefold())
    de_scan = Scan()
    de_index: dict[str, dict[str, Any]] = {}
    if de_path is not None and needed_de:
        de_index = build_de_index(de_path, needed_de, de_scan, max_lines)

    analyses: dict[str, dict[str, Any]] = {}
    defect_fields = {"lossy_sense": 0, "lossy_form": 0, "lossy_record": 0}
    for key in key_classes:
        rec = captured.get(key)
        if rec is None:
            continue
        analysis = analyze_entry(rec, de_index, errors)
        analysis["classes"] = sorted(key_classes[key])
        analyses[key] = analysis
        for s in _as_list(rec.get("senses")):
            if isinstance(s, dict):
                defect_fields["lossy_sense"] += sum(
                    1 for f in LOSSY_SENSE_FIELDS if s.get(f) is not None
                )
        for f in _as_list(rec.get("forms")):
            if isinstance(f, dict):
                defect_fields["lossy_form"] += sum(
                    1 for name in LOSSY_FORM_FIELDS if f.get(name) is not None
                )
        defect_fields["lossy_record"] += sum(
            1 for name in LOSSY_RECORD_FIELDS if rec.get(name) is not None
        )

    core = [
        analyses[k]
        for k, classes in key_classes.items()
        if "core" in classes and k in analyses
    ]
    stratified: dict[str, list[dict[str, Any]]] = {
        c: [analyses[k] for k, classes in key_classes.items() if c in classes and k in analyses]
        for c in STRATIFIED_CLASSES
    }

    by_pos: dict[str, dict[str, Any]] = {}
    for pos in CORE_POS:
        subset = [a for a in core if a["pos"] == pos]
        if subset:
            by_pos[pos] = compute_metrics(subset)

    freedict: dict[str, Any] = {"status": "N/A"}
    if freedict_path is not None:
        needed_en = {a["word"].casefold() for a in core if a["word"]}
        fd_index, fd_scanned = parse_freedict_tei(freedict_path, needed_en)
        matched = [a for a in core if a["word"].casefold() in fd_index]
        fd_de = sum(len(fd_index[a["word"].casefold()]) for a in matched)
        overlap = 0
        partial = 0
        agree_disagree = []
        for a in matched:
            fd_words = {t["text"].casefold() for t in fd_index[a["word"].casefold()]}
            wt_words = {str(w).casefold() for w in a["distinct_de"]}
            if wt_words and fd_words:
                if fd_words == wt_words:
                    overlap += 1
                elif fd_words & wt_words:
                    partial += 1
                else:
                    agree_disagree.append({"word": a["word"], "freedict": sorted(fd_words)})
        freedict = {
            "status": "MEASURED",
            "entries_scanned": fd_scanned,
            "entries_matched": len(matched),
            "german_equivalents": fd_de,
            "exact_set_agreement_with_wiktextract": overlap,
            "partial_agreement": partial,
            "disagreements_sample": agree_disagree[:20],
            "metrics": {
                "headword_match_coverage": _metric(
                    "freedict", len(matched), len(core),
                    "core entries whose exact headword exists in FreeDict",
                ),
                "gender_coverage": _metric(
                    "freedict",
                    sum(1 for t in _fd_all(fd_index, matched) if t.get("gen")),
                    max(1, fd_de),
                    "FreeDict German equivalents carrying a gen element",
                ),
            },
        }

    error_counts: dict[str, int] = {}
    for err in errors:
        error_counts[err["class"]] = error_counts.get(err["class"], 0) + 1

    return {
        "procedure_version": PROCEDURE_VERSION,
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scans": {
            "en": {"lines": en_scan.lines, "records": en_scan.records,
                   "parse_errors": en_scan.parse_errors},
            "de": {"lines": de_scan.lines, "records": de_scan.records,
                   "parse_errors": de_scan.parse_errors},
        },
        "counts": {
            "sample_entries": len(key_classes),
            "records_captured": len(captured),
            "missing_records": len(missing),
            "core_scored": len(core),
            "stratified_scored": {c: len(v) for c, v in stratified.items()},
        },
        "core": compute_metrics(core),
        "by_pos": by_pos,
        "stratified": {c: compute_metrics(v) for c, v in stratified.items() if v},
        "freedict": freedict,
        "field_fidelity": {
            "lossy_sense_fields": defect_fields["lossy_sense"],
            "lossy_form_fields": defect_fields["lossy_form"],
            "lossy_record_fields": defect_fields["lossy_record"],
            "unmapped_fields": {
                "senses": list(LOSSY_SENSE_FIELDS),
                "forms": list(LOSSY_FORM_FIELDS),
                "record": list(LOSSY_RECORD_FIELDS),
            },
        },
        "errors": {
            "counts": error_counts,
            "by_class": {
                cls: [e for e in errors if e["class"] == cls][:50]
                for cls in error_counts
            },
        },
        "per_entry": sorted(analyses.values(), key=lambda a: (a["classes"][0], a["word"])),
    }


def _fd_all(
    fd_index: dict[str, list[dict[str, Any]]], matched: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for a in matched:
        out.extend(fd_index.get(a["word"].casefold(), []))
    return out


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Any, *, overwrite: bool = True) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False)
    path.write_text(text + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only English -> German coverage pilot")
    parser.add_argument("--en", type=Path, required=True, help="English Wiktextract JSONL(.gz)")
    parser.add_argument("--de", type=Path, default=None, help="German Wiktextract JSONL(.gz)")
    parser.add_argument("--freedict", type=Path, default=None, help="FreeDict eng-deu TEI file")
    parser.add_argument(
        "--sample",
        type=Path,
        default=Path("data/processed/pilot-sample.json"),
        help="sample file (read if present, else written)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("data/processed/pilot-coverage.json"),
        help="report output file",
    )
    parser.add_argument(
        "--rebuild-sample",
        action="store_true",
        help="rebuild the sample even if the sample file already exists",
    )
    parser.add_argument(
        "--no-score",
        action="store_true",
        help="only build/refresh the sample, do not score",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=None,
        help="limit lines read per pass (testing only)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sample_path: Path = args.sample

    def log(message: str) -> None:
        print(message, file=sys.stderr)

    if sample_path.exists() and not args.rebuild_sample:
        log(f"using existing sample: {sample_path}")
        sample = json.loads(sample_path.read_text(encoding="utf-8"))
    else:
        if sample_path.exists():
            log(f"rebuilding sample (explicit --rebuild-sample): {sample_path}")
        log("scanning English artefact to build sample ...")
        sample, scan, _info = build_sample(args.en, args.max_lines)
        _write_json(sample_path, sample, overwrite=args.rebuild_sample)
        log(
            f"sample written: {sample_path} "
            f"(core_population={scan.records} records, "
            f"selected={len(sample['entries'])})"
        )

    if args.no_score:
        return 0

    log("scoring sample ...")
    report = score_sample(sample, args.en, args.de, args.freedict, max_lines=args.max_lines)
    report["sample"] = str(sample_path)
    report["inputs"] = {
        "en": {"path": str(args.en), "url": URLS["en"], "sha256": sha256_file(args.en)},
        "de": (
            {"path": str(args.de), "url": URLS["de"], "sha256": sha256_file(args.de)}
            if args.de
            else None
        ),
        "freedict": (
            {"path": str(args.freedict), "url": URLS["freedict"]} if args.freedict else None
        ),
    }
    report["licences"] = {
        "en_wiktionary_jsonl": "UNVERIFIED",
        "de_wiktionary_jsonl": "UNVERIFIED",
        "freedict_eng_deu": "VERIFIED_DATASET_GPL3_AGPL3",
        "note": (
            "kaikki raw pages publish no per-file data licence (citation only); "
            "FreeDict eng-deu TEI header states GPLv3 + AGPLv3 dual licensing."
        ),
    }
    report["recommendation"] = {
        "pilot": "CONDITIONAL_GO",
        "production_import": "NO_GO",
        "reason": "read-only metrics collected; L1 (kaikki file licence) and L3 "
        "(share-alike/GPL compatibility) remain open.",
    }
    _write_json(args.report, report, overwrite=True)
    counts = report["counts"]
    parse_errors = report["scans"]["en"]["parse_errors"]
    log(
        f"report written: {args.report} "
        f"(core_scored={counts['core_scored']}, captured={counts['records_captured']}, "
        f"missing={counts['missing_records']}, parse_errors={parse_errors})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
