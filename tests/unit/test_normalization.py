"""Normalization unit tests (text + import record normalization)."""

from __future__ import annotations

import pytest

from german_morphology import normalize
from scripts.normalized import RecordValidationError, normalize_dictionary, normalize_frequency


def test_lowercases_and_strips() -> None:
    assert normalize("  Häusern  ") == "häusern"
    assert normalize("GEHEN") == "gehen"


def test_preserves_umlauts_without_transliteration() -> None:
    assert normalize("über") == "über"
    assert normalize("Öl") == "öl"
    assert normalize("Ärzte") == "ärzte"
    assert "ueber" not in normalize("über")


def test_preserves_sharp_s() -> None:
    assert normalize("Straße") == "straße"


def test_nfc_normalization() -> None:
    decomposed = "é"
    assert normalize(decomposed) == "é"


def test_collapses_internal_whitespace() -> None:
    assert normalize("a \t  b") == "a b"


def _minimal_dictionary() -> dict:
    return {
        "version": 1,
        "lexemes": [
            {
                "lemma": "  Haus ",
                "part_of_speech": "noun",
                "gender": "neut",
                "senses": [{"sense_index": 1, "definition": "house"}],
                "forms": [],
            },
            {
                "lemma": "Wohnung",
                "part_of_speech": "noun",
                "gender": "fem",
                "senses": [{"sense_index": 1, "definition": "flat, apartment"}],
                "forms": [{"surface": "Wohnung", "form_type": "lemma"}],
                "relations": [{"relation_type": "synonym", "target_lemma": "Haus"}],
            },
        ],
    }


def test_missing_lemma_form_is_derived() -> None:
    data = normalize_dictionary(_minimal_dictionary())
    haus = next(lex for lex in data.lexemes if lex.lemma == "Haus")
    assert [form.surface for form in haus.forms] == ["Haus"]


def test_lemma_is_trimmed_and_validated() -> None:
    data = normalize_dictionary(_minimal_dictionary())
    assert all(not lex.lemma.startswith(" ") for lex in data.lexemes)


def test_unknown_relation_target_rejected() -> None:
    raw = _minimal_dictionary()
    raw["lexemes"][1]["relations"][0]["target_lemma"] = "missing"
    with pytest.raises(RecordValidationError, match="not in dictionary"):
        normalize_dictionary(raw)


def test_duplicate_sense_index_rejected() -> None:
    raw = _minimal_dictionary()
    raw["lexemes"][0]["senses"].append({"sense_index": 1, "definition": "dup"})
    with pytest.raises(RecordValidationError, match="duplicate sense_index"):
        normalize_dictionary(raw)


def test_unknown_part_of_speech_rejected() -> None:
    raw = _minimal_dictionary()
    raw["lexemes"][0]["part_of_speech"] = "nonsense"
    with pytest.raises(RecordValidationError, match="part_of_speech"):
        normalize_dictionary(raw)


def test_validation_error_lists_locations() -> None:
    raw = _minimal_dictionary()
    raw["lexemes"][0]["part_of_speech"] = "nonsense"
    with pytest.raises(RecordValidationError) as excinfo:
        normalize_dictionary(raw)
    assert "lexemes.0.part_of_speech" in str(excinfo.value)


def test_frequency_requires_existing_structure() -> None:
    data = normalize_frequency(
        {"version": 1, "corpus": "c", "entries": [{"lemma": "Haus", "rank": 1, "count": 10}]}
    )
    assert data.entries[0].lemma == "Haus"


def test_frequency_rejects_duplicates() -> None:
    with pytest.raises(RecordValidationError, match="duplicate lemma/surface"):
        normalize_frequency(
            {
                "version": 1,
                "corpus": "c",
                "entries": [
                    {"lemma": "Haus", "rank": 1, "count": 10},
                    {"lemma": "Haus", "rank": 2, "count": 5},
                ],
            }
        )
