"""Import pipeline tests: raw -> normalize -> validate -> processed -> DB."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from scripts.dbload import DatabaseLoader
from scripts.normalized import RecordValidationError, dumps, normalize_dictionary

# `scripts.import` is not addressable with dotted syntax (keyword); import
# the module dynamically instead.
pipeline = importlib.import_module("scripts.import.pipeline")
process_dictionary = pipeline.process_dictionary
read_raw = pipeline.read_raw


def _raw_dictionary() -> dict:
    return {
        "version": 1,
        "lexemes": [
            {
                "lemma": "  Taube ",
                "part_of_speech": "noun",
                "gender": "fem",
                "senses": [{"sense_index": 1, "definition": "pigeon"}],
                "forms": [{"surface": "Taube", "form_type": "lemma"}],
                "examples": [
                    {
                        "text": "Die Taube sitzt auf dem Dach.",
                        "linked_forms": [{"lemma": "Taube", "surface": "Taube"}],
                    }
                ],
            }
        ],
    }


def test_raw_file_is_never_modified(tmp_path: Path) -> None:
    source = tmp_path / "raw" / "dictionary.json"
    processed = tmp_path / "processed" / "dictionary.json"
    source.parent.mkdir(parents=True)
    original = json.dumps(_raw_dictionary(), ensure_ascii=False, indent=2)
    source.write_text(original, encoding="utf-8")
    before = source.read_bytes()

    process_dictionary(source, processed)

    assert source.read_bytes() == before
    assert processed.is_file()


def test_processed_output_is_deterministic(tmp_path: Path) -> None:
    source = tmp_path / "dictionary.json"
    source.write_text(json.dumps(_raw_dictionary()), encoding="utf-8")
    out1 = tmp_path / "processed1.json"
    out2 = tmp_path / "processed2.json"

    process_dictionary(source, out1)
    process_dictionary(source, out2)

    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")


def test_normalization_trims_lemma_and_adds_missing_forms() -> None:
    data = normalize_dictionary(_raw_dictionary())
    assert data.lexemes[0].lemma == "Taube"
    assert [form.surface for form in data.lexemes[0].forms] == ["Taube"]


def test_missing_raw_file_has_helpful_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="data/raw"):
        read_raw(tmp_path / "absent.json")


def test_invalid_record_set_raises_with_context() -> None:
    raw = _raw_dictionary()
    raw["lexemes"][0]["senses"] = []
    with pytest.raises(RecordValidationError) as excinfo:
        normalize_dictionary(raw)
    assert "lexemes.0.senses" in str(excinfo.value)


def test_dictionary_loader_reports_unknown_relation(tmp_path: Path, session) -> None:  # type: ignore[no-untyped-def]
    raw = _raw_dictionary()
    raw["lexemes"].append(
        {
            "lemma": "Sperling",
            "part_of_speech": "noun",
            "gender": "masc",
            "senses": [{"sense_index": 1, "definition": "sparrow"}],
            "forms": [{"surface": "Sperling", "form_type": "lemma"}],
        }
    )
    raw["lexemes"][0]["relations"] = [{"relation_type": "synonym", "target_lemma": "Sperling"}]
    data = normalize_dictionary(raw)  # valid at validation time...
    data.lexemes.pop(1)  # ...then the target disappears (simulated drift)
    report = DatabaseLoader(session).load_dictionary(data)
    assert report.errors
    assert "unresolved relation target" in report.errors[0]
    session.rollback()


def test_frequency_loader_flags_unknown_lemma(session) -> None:  # type: ignore[no-untyped-def]
    from scripts.normalized import NormalizedFrequency

    data = NormalizedFrequency.model_validate(
        {"version": 1, "corpus": "c", "entries": [{"lemma": "Unknownx", "rank": 1, "count": 1}]}
    )
    report = DatabaseLoader(session).load_frequency(data)
    assert report.errors == ["frequency: unknown lemma 'Unknownx'"]
    session.rollback()


def test_dumps_is_utf8_unescaped() -> None:
    data = normalize_dictionary(_raw_dictionary())
    payload = dumps(data)
    assert "Taube" in payload
    assert "\\u" not in payload
