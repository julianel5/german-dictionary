"""Read-only English -> German common-vocabulary coverage study (evaluation only).

Companion to ``pilot_coverage.py``: whereas the pilot measured coverage over a
uniform sample of *raw* en.wiktionary entries (dominated by rare words), this
script measures coverage over a **curated list of common English lemmas** — the
vocabulary a person would actually look up in an English -> German dictionary.
The method is specified in ``docs/data-import/common-words-study.md``.

It never writes to the database, never changes the application, and never
imports external data. It streams the local Wiktextract JSONL artefacts and the
FreeDict TEI source (from the earlier pilot working directory) and reports
coverage/quality metrics **per source** (en.wiktionary, de.wiktionary
enrichment, FreeDict) and **per vocabulary category**.

Contract::

    python -m scripts.import.common_coverage \
      --en       <external>/en/raw-wiktextract-data.jsonl.gz \
      --de       <external>/de/raw-wiktextract-data.jsonl.gz \
      --freedict <external>/freedict/extracted/eng-deu/eng-deu.tei \
      --lemmas   data/processed/common-lemmas.tsv \
      --report   data/processed/common-words-coverage.json

The ``--lemmas`` file is UTF-8 text, one lemma per line: ``word`` optionally
followed by a tab and a category (``noun``, ``verb``, ``adj``, ``adv``,
``function``, ``other``). Lines starting with ``#`` are comments; they are
recorded verbatim in the report so the list is self-describing (provenance
lives in the file header, not in the code). When a category is absent the
script derives it from the English data's own POS tags and marks
``category_source == "derived"``.

Language policy and identity rules are the same as the pilot: records are
classified by their own ``lang_code`` (``en`` headwords, ``de`` enrichment);
homonymous records (same word, different ``etymology_number``) are kept
separate and **never merged**; every lemma is also checked for the
"inflected-only" condition (the token exists only as an inflected form of
another English lemma), which is reported, not silently dropped.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.paths import ensure_paths

_pilot = importlib.import_module("scripts.import.pilot_coverage")

GENDER_TAGS = _pilot.GENDER_TAGS
Scan = _pilot.Scan
_as_list = _pilot._as_list
_metric = _pilot._metric
_write_json = _pilot._write_json
analyze_entry = _pilot.analyze_entry
build_de_index = _pilot.build_de_index
iter_records = _pilot.iter_records
parse_freedict_tei = _pilot.parse_freedict_tei
record_key = _pilot.record_key
sha256_file = _pilot.sha256_file

ensure_paths()

PROCEDURE_VERSION = "common-words-coverage/1.0"
CORE_POS = ("noun", "verb", "adj", "adv")
FUNCTION_POS = {
    "article",
    "conj",
    "conjunction",
    "contraction",
    "det",
    "determiner",
    "interj",
    "interjection",
    "numeral",
    "particle",
    "prep",
    "preposition",
    "pron",
    "pronoun",
}
LEMMA_CATEGORIES = (*CORE_POS, "function", "other")

URLS = {
    "en": "https://kaikki.org/dictionary/raw-wiktextract-data.jsonl.gz",
    "de": "https://kaikki.org/dewiktionary/raw-wiktextract-data.jsonl.gz",
    "freedict": (
        "https://download.freedict.org/dictionaries/eng-deu/1.9-fd1/"
        "freedict-eng-deu-1.9-fd1.src.tar.xz"
    ),
}


def derive_category(pos: str) -> str:
    """Map a source POS tag to a coarse product category."""
    if pos in CORE_POS:
        return pos
    if pos in FUNCTION_POS:
        return "function"
    return "other"


def read_lemma_list(path: Path) -> tuple[list[dict[str, str | None]], list[str]]:
    """Read the curated lemma list.

    Accepted row shapes (UTF-8 TSV; ``#`` lines are recorded as provenance):
    ``word``, ``word<TAB>category``, or ``word<TAB><TAB>rank:N`` (and any
    combination of the latter two columns, in any order after ``word``).
    """
    entries: list[dict[str, str | None]] = []
    header: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            header.append(line[1:].strip())
            continue
        parts = [part.strip() for part in line.split("\t")]
        word = parts[0] if parts else ""
        if not word:
            continue
        entry: dict[str, str | None] = {"word": word, "category": None}
        for extra in parts[1:]:
            if not extra:
                continue
            if extra in LEMMA_CATEGORIES:
                entry["category"] = extra
            elif extra.startswith("rank:"):
                entry["rank"] = extra[len("rank:"):]
            else:
                raise ValueError(
                    f"unknown field {extra!r} for {word!r} "
                    f"(expected a category in {LEMMA_CATEGORIES} or 'rank:N')"
                )
        entries.append(entry)
    return entries, header


def scan_en_lemma_records(
    en_path: Path,
    lemmas: list[dict[str, str | None]],
    scan: Scan,
    max_lines: int | None = None,
) -> tuple[dict[str, list[tuple[str, dict[str, Any]]]], dict[str, list[str]]]:
    """Collect, per lemma, its English records and any lemma used as a form.

    Returns ``(lemma_records, form_uses)`` where ``lemma_records[norm]`` is a
    list of ``(identity_key, record)`` tuples (homonyms kept separate) and
    ``form_uses[norm]`` lists identity keys of records that list ``norm`` as an
    inflected form.
    """
    needed = {str(entry["word"]).casefold() for entry in lemmas}
    lemma_records: dict[str, list[tuple[str, dict[str, Any]]]] = {
        norm: [] for norm in needed
    }
    form_uses: dict[str, list[str]] = {}
    for rec in iter_records(en_path, scan, max_lines):
        if rec.get("lang_code") != "en":
            continue
        word = rec.get("word")
        if not word:
            continue
        norm = str(word).casefold()
        key = record_key(rec)
        if norm in lemma_records:
            lemma_records[norm].append((key, rec))
        for form in _as_list(rec.get("forms")):
            if not isinstance(form, dict):
                continue
            form_text = form.get("form")
            if not form_text:
                continue
            fnorm = str(form_text).casefold()
            if fnorm in needed and (not form_uses.get(fnorm) or key not in form_uses[fnorm]):
                form_uses.setdefault(fnorm, []).append(key)
    return lemma_records, form_uses


def analyze_lemma(
    entry: dict[str, str | None],
    records: list[tuple[str, dict[str, Any]]],
    errors: list[dict[str, Any]],
) -> dict[str, Any]:
    """Lemma-level aggregation over its (separate) homonymous records."""
    word = str(entry["word"])
    list_category = entry.get("category")
    analyses: list[dict[str, Any]] = []
    distinct_de: set[str] = set()
    pos_counter: Counter[str] = Counter()
    senses_total = 0
    examples_total = 0
    examples_with_translation = 0
    has_definition = False
    has_irregular_tag = False
    has_conjugated_forms = False
    for key, rec in records:
        analysis = analyze_entry(rec, {}, errors)
        analysis["identity"] = key
        analyses.append(analysis)
        pos_counter[str(rec.get("pos") or "")] += 1
        distinct_de.update(analysis["distinct_de"])
        senses_total += analysis["senses_total"]
        examples_total += analysis["examples_total"]
        examples_with_translation += analysis["examples_with_translation"]
        has_definition = has_definition or bool(analysis["has_definition"])
        if "irregular" in {str(t) for t in _as_list(rec.get("tags"))}:
            has_irregular_tag = True
        for form in _as_list(rec.get("forms")):
            if not isinstance(form, dict):
                continue
            form_tags = {str(t) for t in _as_list(form.get("tags"))}
            if "irregular" in form_tags:
                has_irregular_tag = True
            if "past" in form_tags or "participle" in form_tags:
                has_conjugated_forms = True

    pos_observed = sorted(pos_counter)
    dominant_pos = ""
    if pos_counter:
        dominant_pos = sorted(pos_counter.items(), key=lambda item: (-item[1], item[0]))[0][0]
    category = (
        list_category
        if list_category is not None
        else derive_category(dominant_pos)
    )
    verb_type: str | None = None
    if category == "verb" or dominant_pos == "verb":
        verb_type = (
            "irregular"
            if has_irregular_tag
            else ("conjugated" if has_conjugated_forms else "minimal")
        )
    de_words = sorted(distinct_de)

    return {
        "word": word,
        "norm_word": word.casefold(),
        "rank": entry.get("rank"),
        "category": category,
        "category_source": "list" if list_category is not None else "derived",
        "dominant_pos": dominant_pos,
        "pos_observed": pos_observed,
        "present": bool(records),
        "records_matched": len(records),
        "senses_total": senses_total,
        "has_definition": has_definition,
        "has_de": bool(de_words),
        "de_words": de_words,
        "distinct_de_count": len(de_words),
        "multiple_de": len(de_words) >= 2,
        "examples_total": examples_total,
        "examples_with_translation": examples_with_translation,
        "verb_type": verb_type,
        "surface": {
            "is_ascii_alpha": word.isascii() and word.isalpha(),
            "has_space": " " in word,
            "has_hyphen": "-" in word,
        },
        "records": analyses,
    }


def attach_de_enrichment(
    lemma: dict[str, Any], de_index: dict[str, dict[str, Any]]
) -> None:
    """Fill de-edition enrichment fields for the lemma's German equivalents."""
    matched = {norm: de_index[norm] for norm in lemma["de_words"] if norm in de_index}
    lemma["de_words_total"] = len(lemma["de_words"])
    lemma["de_matched"] = len(matched)
    lemma["de_gender_labels"] = sum(
        1 for m in matched.values() if any(t in GENDER_TAGS for t in _as_list(m.get("gender_tags")))
    )
    lemma["de_with_forms"] = sum(1 for m in matched.values() if m.get("form_count", 0) > 0)
    lemma["de_with_gloss"] = sum(1 for m in matched.values() if m.get("has_gloss"))


def attach_freedict(lemma: dict[str, Any], fd_index: dict[str, list[dict[str, Any]]]) -> None:
    """Fill FreeDict fields and the exclusive-contribution bucket."""
    equivalents = fd_index.get(lemma["norm_word"], [])
    lemma["fd_present"] = lemma["norm_word"] in fd_index
    lemma["fd_equivalents"] = equivalents
    lemma["fd_de_count"] = len(equivalents)
    lemma["fd_genders"] = sum(1 for t in equivalents if t.get("gen"))
    en = lemma["has_de"]
    fd_de = lemma["fd_de_count"] > 0
    if en and fd_de:
        bucket = "both"
    elif en:
        bucket = "en_only"
    elif fd_de:
        bucket = "freedict_only"
    else:
        bucket = "neither"
    lemma["exclusive"] = bucket


def lemma_metrics(lemmas: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Aggregate metrics over a lemma set (mirrors the pilot's metric style)."""
    entries = len(lemmas)
    if entries == 0:
        return {"lemmas_scored": _metric("all", 0, 0)}
    present = sum(1 for lemma in lemmas if lemma["present"])
    has_de = sum(1 for lemma in lemmas if lemma["has_de"])
    fd_present = sum(1 for lemma in lemmas if lemma["fd_present"])
    fd_de = sum(1 for lemma in lemmas if lemma["fd_de_count"] > 0)
    any_de = sum(1 for lemma in lemmas if lemma["has_de"] or lemma["fd_de_count"] > 0)
    de_total = sum(lemma["de_words_total"] for lemma in lemmas)
    de_matched = sum(lemma["de_matched"] for lemma in lemmas)
    examples_total = sum(lemma["examples_total"] for lemma in lemmas)
    return {
        "lemmas_scored": _metric("all", entries, entries),
        "en_headword_present": _metric(
            "en",
            present,
            entries,
            "record with lang_code == en and word == lemma exists",
        ),
        "en_de_coverage": _metric(
            "en",
            has_de,
            entries,
            "lemma carries >=1 German translation (code == de) in en.wiktionary",
        ),
        "freedict_headword_present": _metric(
            "freedict", fd_present, entries, "exact headword present in FreeDict"
        ),
        "freedict_de_coverage": _metric(
            "freedict", fd_de, entries, ">=1 German equivalent from FreeDict"
        ),
        "any_source_de_coverage": _metric(
            "all",
            any_de,
            entries,
            "German equivalent from en.wiktionary or FreeDict",
        ),
        "definition_coverage": _metric(
            "en",
            sum(1 for lemma in lemmas if lemma["has_definition"]),
            entries,
            ">=1 English gloss in en.wiktionary",
        ),
        "multiple_german_equivalents": _metric(
            "en",
            sum(1 for lemma in lemmas if lemma["multiple_de"]),
            entries,
            ">=2 distinct German surfaces (casefolded) from en.wiktionary",
        ),
        "de_enrichment_matched": _metric(
            "de",
            de_matched,
            de_total,
            "German equivalents found by exact casefold match in the de edition",
        ),
        "de_enrichment_gender": _metric(
            "de",
            sum(lemma["de_gender_labels"] for lemma in lemmas),
            de_matched,
            "matched de-edition records with a top-level gender tag",
        ),
        "de_enrichment_forms": _metric(
            "de",
            sum(lemma["de_with_forms"] for lemma in lemmas),
            de_matched,
            "matched de-edition records carrying >=1 form",
        ),
        "de_enrichment_gloss": _metric(
            "de",
            sum(lemma["de_with_gloss"] for lemma in lemmas),
            de_matched,
            "matched de-edition records carrying >=1 German gloss",
        ),
        "example_coverage": _metric(
            "en",
            sum(1 for lemma in lemmas if lemma["examples_total"] > 0),
            entries,
            "lemma has >=1 sense example",
        ),
        "example_translation_coverage": _metric(
            "en",
            sum(lemma["examples_with_translation"] for lemma in lemmas),
            examples_total,
            "examples carrying a translation field",
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only English -> German common-vocabulary coverage study"
    )
    parser.add_argument("--en", type=Path, required=True, help="English Wiktextract JSONL(.gz)")
    parser.add_argument("--de", type=Path, default=None, help="German Wiktextract JSONL(.gz)")
    parser.add_argument("--freedict", type=Path, default=None, help="FreeDict eng-deu TEI file")
    parser.add_argument("--lemmas", type=Path, required=True, help="curated lemma list file")
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("data/processed/common-words-coverage.json"),
        help="report output file",
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

    def log(message: str) -> None:
        print(message, file=sys.stderr)

    lemmas, header = read_lemma_list(args.lemmas)
    seen: set[str] = set()
    unique: list[dict[str, str | None]] = []
    duplicates = 0
    for entry in lemmas:
        norm = str(entry["word"]).casefold()
        if norm in seen:
            duplicates += 1
            continue
        seen.add(norm)
        unique.append(entry)
    log(f"lemmas: {len(lemmas)} requested, {len(unique)} unique, {duplicates} duplicates")

    en_scan = Scan()
    de_scan = Scan()
    log("scanning English artefact ...")
    lemma_records, form_uses = scan_en_lemma_records(args.en, unique, en_scan, args.max_lines)

    errors: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    inflected_only: dict[str, list[str]] = {}
    for entry in unique:
        norm = str(entry["word"]).casefold()
        records = lemma_records.get(norm, [])
        if not records and norm in form_uses:
            inflected_only[norm] = form_uses[norm]
        lemma = analyze_lemma(entry, records, errors)
        lemma["inflected_only"] = norm in inflected_only
        lemma["missing"] = not bool(records)
        results.append(lemma)

    needed_de: set[str] = (
        set().union(*(lemma["de_words"] for lemma in results)) if results else set()
    )
    de_index: dict[str, dict[str, Any]] = {}
    if args.de is not None and needed_de:
        log(f"scanning German artefact ({len(needed_de)} needed lemmas) ...")
        de_index = build_de_index(args.de, needed_de, de_scan, args.max_lines)
    for lemma in results:
        attach_de_enrichment(lemma, de_index)

    fd_index: dict[str, list[dict[str, Any]]] = {}
    fd_scanned = 0
    if args.freedict is not None:
        log(f"scanning FreeDict ({len(results)} needed headwords) ...")
        fd_index, fd_scanned = parse_freedict_tei(
            args.freedict, {lemma["norm_word"] for lemma in results}
        )
    for lemma in results:
        attach_freedict(lemma, fd_index)

    categories = sorted({lemma["category"] for lemma in results})
    per_category: dict[str, dict[str, dict[str, Any]]] = {
        category: lemma_metrics([lemma for lemma in results if lemma["category"] == category])
        for category in categories
    }
    pos_labels = (*CORE_POS, "function", "other", "")
    by_pos: dict[str, dict[str, dict[str, Any]]] = {}
    for pos in pos_labels:
        subset = [lemma for lemma in results if lemma["dominant_pos"] == pos]
        if subset:
            by_pos[pos or "no_pos"] = lemma_metrics(subset)

    exclusive = Counter(lemma["exclusive"] for lemma in results)
    error_counts = Counter(error["class"] for error in errors)

    report = {
        "procedure_version": PROCEDURE_VERSION,
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "inputs": {
            "en": {"path": str(args.en), "url": URLS["en"], "sha256": sha256_file(args.en)},
            "de": (
                {"path": str(args.de), "url": URLS["de"], "sha256": sha256_file(args.de)}
                if args.de
                else None
            ),
            "freedict": (
                {"path": str(args.freedict), "url": URLS["freedict"]} if args.freedict else None
            ),
            "lemmas": {
                "path": str(args.lemmas),
                "sha256": sha256_file(args.lemmas),
                "header": header,
                "format": "word[TAB]category; comments start with '#'",
            },
        },
        "scans": {
            "en": {
                "lines": en_scan.lines,
                "records": en_scan.records,
                "parse_errors": en_scan.parse_errors,
            },
            "de": {
                "lines": de_scan.lines,
                "records": de_scan.records,
                "parse_errors": de_scan.parse_errors,
            },
        },
        "counts": {
            "lemmas_requested": len(lemmas),
            "lemmas_unique": len(unique),
            "duplicate_entries_removed": duplicates,
            "lemmas_with_records": sum(1 for lemma in results if lemma["present"]),
            "lemmas_missing_from_en": sum(1 for lemma in results if lemma["missing"]),
            "lemmas_inflected_only_nonheadword": len(inflected_only),
            "lemmas_non_alphabetic_surface": sum(
                1 for lemma in results if not lemma["surface"]["is_ascii_alpha"]
            ),
            "lemmas_with_space": sum(1 for lemma in results if lemma["surface"]["has_space"]),
            "lemmas_with_hyphen": sum(1 for lemma in results if lemma["surface"]["has_hyphen"]),
            "records_matched": sum(lemma["records_matched"] for lemma in results),
        },
        "metrics": {"all": lemma_metrics(results), "per_category": per_category, "by_pos": by_pos},
        "exclusive_contribution": {
            "counts": dict(exclusive),
            "pct": {k: round(100.0 * v / len(results), 2) for k, v in exclusive.items()},
        },
        "freedict": {
            "status": "MEASURED" if args.freedict is not None else "N/A",
            "entries_scanned": fd_scanned,
            "headwords_matched": sum(1 for lemma in results if lemma["fd_present"]),
            "german_equivalents_total": sum(lemma["fd_de_count"] for lemma in results),
            "gender_tagged": sum(lemma["fd_genders"] for lemma in results),
        },
        "de_enrichment": {
            "status": "MEASURED" if args.de is not None else "N/A",
            "equivalents_needed": sum(lemma["de_words_total"] for lemma in results),
            "matched": sum(lemma["de_matched"] for lemma in results),
        },
        "defects": {
            "counts": dict(error_counts),
            "by_class": {
                cls: [error for error in errors if error["class"] == cls][:50]
                for cls in error_counts
            },
        },
        "licences": {
            "en_wiktionary_jsonl": "UNVERIFIED",
            "de_wiktionary_jsonl": "UNVERIFIED",
            "freedict_eng_deu": "VERIFIED_DATASET_GPL3_AGPL3",
            "note": (
                "kaikki raw pages publish no per-file data licence (citation only); "
                "FreeDict eng-deu TEI header states GPLv3 + AGPLv3 dual licensing."
            ),
        },
        "recommendation": {
            "common_words_measurement": "MEASURED",
            "production_import": "NO_GO",
            "remaining_blockers": ["L1", "L3", "L4"],
            "note": (
                "aggregate interpretation lives in docs/data-import/common-words-study.md; "
                "the lemma list and raw per-lemma detail are provenance artefacts, not "
                "committed to the repository."
            ),
        },
        "per_lemma": sorted(results, key=lambda lemma: (lemma["category"], lemma["word"])),
    }
    _write_json(args.report, report, overwrite=True)
    log(
        f"report written: {args.report} (lemmas={len(unique)}, "
        f"present={sum(1 for lemma in results if lemma['present'])}, records_matched="
        f"{sum(lemma['records_matched'] for lemma in results)}, "
        f"missing={sum(1 for lemma in results if lemma['missing'])}, "
        f"parse_errors={en_scan.parse_errors})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())