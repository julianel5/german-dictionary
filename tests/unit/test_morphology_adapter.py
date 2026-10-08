"""Morphology adapter tests: protocol, factory, fixture engine, spaCy engine."""

from __future__ import annotations

import functools

import pytest

from german_morphology import (
    GrammaticalFeatures,
    MorphologicalAnalysis,
    MorphologyEngine,
    create_morphology_engine,
)
from german_morphology.fixture_engine import FixtureMorphologyEngine


def test_fixture_engine_satisfies_protocol() -> None:
    engine = FixtureMorphologyEngine()
    assert isinstance(engine, MorphologyEngine)
    assert engine.name == "fixture"


def test_fixture_engine_resolves_critical_forms() -> None:
    engine = FixtureMorphologyEngine()
    expectations = {
        "ging": ("gehen", "Past"),
        "gingen": ("gehen", "Past"),
        "gegangen": ("gehen", None),
        "Häusern": ("Haus", None),
    }
    for surface, (lemma, _tense) in expectations.items():
        analyses = engine.analyze(surface)
        assert analyses, f"no analysis for {surface!r}"
        assert analyses[0].lemma == lemma
        assert analyses[0].normalized_lemma == lemma.lower()


def test_fixture_engine_features_are_structured() -> None:
    engine = FixtureMorphologyEngine()
    ging = engine.analyze("ging")[0]
    assert ging.features.tense == "Past"
    assert ging.features.mood == "Ind"
    assert ging.features.person == "3"
    assert ging.features.number == "Sing"

    hausern = engine.analyze("Häusern")[0]
    assert hausern.features.case == "Dat"
    assert hausern.features.number == "Plur"
    assert hausern.features.gender == "Neut"


def test_fixture_engine_returns_nothing_for_unknown() -> None:
    engine = FixtureMorphologyEngine()
    assert engine.analyze("xyzzy-not-a-word") == []


def test_factory_fixture_and_none() -> None:
    assert create_morphology_engine("fixture").name == "fixture"
    assert create_morphology_engine("none") is None
    with pytest.raises(ValueError):
        create_morphology_engine("does-not-exist")


def test_factory_auto_never_raises() -> None:
    engine = create_morphology_engine("auto")
    assert engine is None or isinstance(engine, MorphologyEngine)


def test_analysis_model_is_engine_independent() -> None:
    analysis = MorphologicalAnalysis(
        surface="ging",
        lemma="gehen",
        normalized_lemma="gehen",
        part_of_speech="verb",
        features=GrammaticalFeatures(tense="Past"),
        confidence=1.0,
        engine="test",
    )
    assert analysis.features.as_dict()["tense"] == "Past"


@functools.lru_cache(maxsize=1)
def _spacy_engine_available() -> bool:
    try:
        from german_morphology.spacy_engine import SpacyMorphologyEngine

        SpacyMorphologyEngine().analyze("gehen")
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _spacy_engine_available(), reason="spaCy German model not installed")
def test_spacy_engine_resolves_critical_forms() -> None:
    """The real German analyzer must lemmatize the milestone-critical forms."""
    from german_morphology.spacy_engine import SpacyMorphologyEngine

    engine = SpacyMorphologyEngine()
    expected_lemma = {
        "ging": "gehen",
        "gingen": "gehen",
        "gegangen": "gehen",
        "Häusern": "Haus",
    }
    for surface, lemma in expected_lemma.items():
        analyses = engine.analyze(surface)
        assert analyses, f"no analysis for {surface!r}"
        assert analyses[0].lemma == lemma, f"{surface!r} -> {analyses[0].lemma!r}"
        assert analyses[0].confidence == 1.0  # never fabricated
        assert isinstance(analyses[0].features, GrammaticalFeatures)


@pytest.mark.skipif(not _spacy_engine_available(), reason="spaCy German model not installed")
def test_spacy_engine_reports_grammatical_features() -> None:
    from german_morphology.spacy_engine import SpacyMorphologyEngine

    analysis = SpacyMorphologyEngine().analyze("ging")[0]
    assert analysis.features.tense == "Past"
    assert analysis.features.number == "Sing"
    assert analysis.part_of_speech == "verb"
