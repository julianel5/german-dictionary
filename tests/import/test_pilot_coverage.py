"""Read-only coverage pilot tests (small synthetic fixtures, no network)."""

from __future__ import annotations

import gzip
import importlib
import json
from pathlib import Path

import pytest

pilot = importlib.import_module("scripts.import.pilot_coverage")


def _write_jsonl(path: Path, records: list[dict], *, gz: bool = False) -> None:
    text = "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n"
    if gz:
        with gzip.open(path, "wt", encoding="utf-8") as handle:
            handle.write(text)
    else:
        path.write_text(text, encoding="utf-8")


def _house() -> dict:
    return {
        "word": "house",
        "pos": "noun",
        "lang": "English",
        "lang_code": "en",
        "senses": [
            {
                "sense_index": 0,
                "glosses": ["A building for people to live in."],
                "tags": ["countable"],
                "translations": [{"code": "de", "word": "Haus", "tags": ["neuter"]}],
                "examples": [{"text": "They bought a house."}],
            }
        ],
        "forms": [{"form": "houses", "tags": ["plural"]}],
        "translations": [{"code": "fr", "word": "maison"}],
    }


def _go() -> dict:
    return {
        "word": "go",
        "pos": "verb",
        "lang_code": "en",
        "etymology_number": 1,
        "senses": [
            {
                "sense_index": 0,
                "glosses": ["to move"],
                "translations": [{"code": "de", "word": "gehen"}],
            }
        ],
        "forms": [{"form": "went", "tags": ["past"]}, {"form": "gone", "tags": ["participle"]}],
    }


def _car() -> dict:
    return {
        "word": "car",
        "pos": "noun",
        "lang_code": "en",
        "senses": [
            {
                "sense_index": 0,
                "glosses": ["a vehicle"],
                "translations": [
                    {"code": "de", "word": "Auto"},
                    {"code": "de", "word": "Wagen"},
                ],
            }
        ],
    }


def _bank(etym: int, *, with_de: bool) -> dict:
    sense = {"sense_index": 0, "glosses": ["bank"], "tags": ["finance"]}
    if with_de:
        sense["translations"] = [{"code": "de", "word": "Bank"}]
    return {
        "word": "bank",
        "pos": "noun",
        "lang_code": "en",
        "etymology_number": etym,
        "senses": [sense],
    }


def _poly() -> dict:
    return {
        "word": "poly",
        "pos": "adj",
        "lang_code": "en",
        "senses": [
            {"sense_index": 0, "glosses": ["one"]},
            {"sense_index": 1, "glosses": ["two"]},
            {"sense_index": 2, "glosses": ["three"]},
        ],
    }


def _seldom() -> dict:
    return {
        "word": "seldom",
        "pos": "adv",
        "lang_code": "en",
        "senses": [{"sense_index": 0, "glosses": ["rarely"]}],
    }


def _en_records() -> list[dict]:
    return [
        _house(),
        _go(),
        _car(),
        _bank(1, with_de=True),
        _bank(2, with_de=False),
        _poly(),
        _seldom(),
        {"word": "maison", "pos": "noun", "lang_code": "fr", "senses": []},
    ]


def test_key_roundtrip_and_record_key() -> None:
    key = pilot.make_key("bank", "noun", "2")
    assert key == "bank\tnoun\t2"
    assert pilot.split_key(key) == ("bank", "noun", "2")
    assert pilot.record_key({"word": "x", "pos": "noun"}) == "x\tnoun\t0"


def test_predicates() -> None:
    assert pilot.is_irregular_verb(_go())
    assert not pilot.is_irregular_verb(_house())
    assert pilot.is_polysemous(_poly())
    assert not pilot.is_polysemous(_house())
    assert pilot.has_sense_multi_de(_car())
    assert not pilot.has_sense_multi_de(_house())
    assert pilot.has_sense_labels(_house())
    assert pilot.has_sense_examples(_house())
    assert not pilot.has_de_translation(_seldom())
    assert pilot.has_de_translation(_house())


def test_select_core_is_deterministic_and_spread() -> None:
    keys = [pilot.make_key(f"w{i:04d}", "noun", "0") for i in range(1000)]
    first = pilot.select_core(keys)
    second = pilot.select_core(list(reversed(keys)))
    assert first == second
    selected, population, stride, offset = first
    assert population == 1000
    assert len(selected) == pilot.CORE_SIZE
    assert stride == 1000 // pilot.CORE_SIZE
    assert offset == pilot.SEED % stride
    assert selected == sorted(selected)


def test_select_core_small_population_returns_all() -> None:
    keys = [pilot.make_key("a", "noun", "0"), pilot.make_key("b", "verb", "0")]
    selected, population, stride, offset = pilot.select_core(keys)
    assert selected == sorted(keys)
    assert (population, stride, offset) == (2, 1, 0)


def test_iter_records_counts_parse_errors(tmp_path: Path) -> None:
    path = tmp_path / "data.jsonl"
    path.write_text('{"word": "ok"}\nnot json\n\n[1,2]\n{"word": "two"}\n', encoding="utf-8")
    scan = pilot.Scan()
    records = list(pilot.iter_records(path, scan))
    assert [r["word"] for r in records] == ["ok", "two"]
    assert scan.parse_errors == 2
    assert scan.records == 2


def test_build_sample_classes_and_shape(tmp_path: Path) -> None:
    en = tmp_path / "en.jsonl.gz"
    _write_jsonl(en, _en_records(), gz=True)
    sample, scan, info = pilot.build_sample(en)
    assert sample["seed"] == pilot.SEED
    by_class: dict[str, list[dict]] = {}
    for entry in sample["entries"]:
        by_class.setdefault(entry["class"], []).append(entry)
    core_words = {e["word"] for e in by_class["core"]}
    assert {"house", "go", "bank", "seldom"} <= core_words
    # two homonyms survive as distinct keys (etymology_number differs)
    bank_keys = [e for e in by_class["core"] if e["word"] == "bank"]
    assert {e["etymology_number"] for e in bank_keys} == {"1", "2"}
    assert {e["word"] for e in by_class["irregular_verb"]} == {"go"}
    assert {e["word"] for e in by_class["multi_de"]} == {"car"}
    assert {e["word"] for e in by_class["no_de"]} >= {"seldom"}
    assert {e["word"] for e in by_class["polysemy"]} == {"poly"}
    assert scan.records == len(_en_records())
    assert info["core_population"] >= 1


def test_german_equivalents_levels() -> None:
    rec = _house()
    rec["translations"].append({"code": "de", "word": "Gebäude", "note": "archaic"})
    eq = pilot.german_equivalents(rec)
    assert {e["level"] for e in eq} == {"headword", "sense"}
    assert {e["word"] for e in eq} == {"Haus", "Gebäude"}


def test_analyze_entry_flags() -> None:
    errors: list[dict] = []
    analysis = pilot.analyze_entry(_seldom(), {}, errors)
    assert analysis["has_de"] is False
    assert any(e["class"] == "no_german_translation" for e in errors)

    errors = []
    rec = _house()
    rec["senses"][0].pop("translations")
    rec["translations"] = [{"code": "de", "note": "only note, no word"}]
    analysis = pilot.analyze_entry(rec, {}, errors)
    classes = {e["class"] for e in errors}
    assert "sense_unmapped" in classes
    assert "word_field_absent" in classes

    errors = []
    pilot.analyze_entry(_car(), {}, errors)
    # duplicate detection applies to identical surfaces only -> none here
    assert not any(e["class"] == "duplicate_translation" for e in errors)


def test_compute_metrics_zero_denominator_is_na() -> None:
    metrics = pilot.compute_metrics([])
    assert metrics["entries_scored"]["status"] == "N/A"


def test_parse_freedict_tei(tmp_path: Path) -> None:
    tei = tmp_path / "sample.tei"
    tei.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>\n'
        '<entry xml:id="house.1"><form><orth>house</orth></form><sense>'
        '<cit type="trans"><quote xml:lang="de">Haus</quote>'
        "<gramGrp><gen>neut</gen></gramGrp></cit></sense></entry>\n"
        '<entry xml:id="cat.1"><form><orth>cat</orth></form><sense>'
        '<cit type="trans"><quote xml:lang="de">Katze</quote>'
        "<gramGrp><gen>fem</gen></gramGrp></cit></sense></entry>\n"
        "</body></text></TEI>\n",
        encoding="utf-8",
    )
    index, scanned = pilot.parse_freedict_tei(tei, {"house"})
    assert scanned == 2
    assert "house" in index
    assert index["house"][0]["text"] == "Haus"
    assert index["house"][0]["gen"] == "neut"
    assert "cat" not in index


def _de_record() -> dict:
    return {
        "word": "Haus",
        "pos": "noun",
        "lang_code": "de",
        "tags": ["neuter"],
        "senses": [{"glosses": ["Gebäude"]}],
        "forms": [{"form": "Häuser", "tags": ["nominative", "plural"]}],
    }


def test_end_to_end_main_builds_and_reuses_sample(tmp_path: Path) -> None:
    en = tmp_path / "en.jsonl.gz"
    de = tmp_path / "de.jsonl.gz"
    freedict = tmp_path / "fd.tei"
    sample = tmp_path / "pilot-sample.json"
    report = tmp_path / "pilot-coverage.json"
    _write_jsonl(en, _en_records(), gz=True)
    _write_jsonl(de, [_de_record()], gz=True)
    freedict.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0"><text><body>'
        '<entry xml:id="house.1"><form><orth>house</orth></form><sense>'
        '<cit type="trans"><quote xml:lang="de">Haus</quote>'
        "<gramGrp><gen>neut</gen></gramGrp></cit></sense></entry>"
        "</body></text></TEI>\n",
        encoding="utf-8",
    )

    argv = [
        "--en", str(en),
        "--de", str(de),
        "--freedict", str(freedict),
        "--sample", str(sample),
        "--report", str(report),
    ]
    assert pilot.main(argv) == 0
    assert sample.is_file()
    assert report.is_file()
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["counts"]["core_scored"] >= 1
    assert payload["core"]["german_translation_coverage"]["status"] == "MEASURED"
    assert payload["freedict"]["status"] == "MEASURED"
    assert payload["licences"]["freedict_eng_deu"].startswith("VERIFIED")
    assert payload["recommendation"]["production_import"] == "NO_GO"

    first_sample_bytes = sample.read_bytes()
    assert pilot.main(argv) == 0  # existing sample is reused, not overwritten
    assert sample.read_bytes() == first_sample_bytes

    sample.write_text('{"entries": [], "sentinel": true}\n', encoding="utf-8")
    assert pilot.main([*argv, "--rebuild-sample"]) == 0
    rebuilt = json.loads(sample.read_text(encoding="utf-8"))
    assert "sentinel" not in rebuilt
    assert len(rebuilt["entries"]) >= 1


def test_main_refuses_to_clobber_without_flag(tmp_path: Path) -> None:
    en = tmp_path / "en.jsonl.gz"
    _write_jsonl(en, _en_records(), gz=True)
    sample = tmp_path / "pilot-sample.json"
    sample.write_text('{"entries": [], "sentinel": true}\n', encoding="utf-8")
    # existing sample is loaded rather than overwritten, so the sentinel survives
    assert pilot.main(["--en", str(en), "--sample", str(sample), "--report",
                       str(tmp_path / "r.json")]) == 0
    assert json.loads(sample.read_text(encoding="utf-8"))["sentinel"] is True


def test_write_json_refuses_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "x.json"
    target.write_text("{}", encoding="utf-8")
    with pytest.raises(FileExistsError):
        pilot._write_json(target, {"a": 1}, overwrite=False)
