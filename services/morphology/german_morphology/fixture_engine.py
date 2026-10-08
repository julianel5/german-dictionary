"""Deterministic fixture-based morphology engine.

This engine exists for tests and fully offline demos. It resolves the
surface forms covered by the project fixture dataset (and a few extra
forms used in integration tests) to lemmas with structured features.
Unknown surfaces return an empty analysis list — results are never
fabricated.
"""

from __future__ import annotations

from german_morphology.text import normalize
from german_morphology.types import (
    GrammaticalFeatures,
    MorphologicalAnalysis,
    make_analysis,
)

_ENGINE_NAME = "fixture"

# surface (normalized) -> (lemma, part_of_speech, features)
_FIXTURE_ENTRIES: dict[str, tuple[str, str, GrammaticalFeatures]] = {
    "gehen": (
        "gehen",
        "verb",
        GrammaticalFeatures(verb_form="Inf"),
    ),
    "gehst": (
        "gehen",
        "verb",
        GrammaticalFeatures(person="2", number="Sing", tense="Pres", mood="Ind", verb_form="Fin"),
    ),
    "geht": (
        "gehen",
        "verb",
        GrammaticalFeatures(person="3", number="Sing", tense="Pres", mood="Ind", verb_form="Fin"),
    ),
    "gehe": (
        "gehen",
        "verb",
        GrammaticalFeatures(person="1", number="Sing", tense="Pres", mood="Ind", verb_form="Fin"),
    ),
    "ging": (
        "gehen",
        "verb",
        GrammaticalFeatures(person="3", number="Sing", tense="Past", mood="Ind", verb_form="Fin"),
    ),
    "gingen": (
        "gehen",
        "verb",
        GrammaticalFeatures(person="3", number="Plur", tense="Past", mood="Ind", verb_form="Fin"),
    ),
    "ginge": (
        "gehen",
        "verb",
        GrammaticalFeatures(person="3", number="Sing", tense="Past", mood="Sub", verb_form="Fin"),
    ),
    "gegangen": (
        "gehen",
        "verb",
        GrammaticalFeatures(verb_form="Part"),
    ),
    "haus": (
        "Haus",
        "noun",
        GrammaticalFeatures(case="Nom", gender="Neut", number="Sing"),
    ),
    "hause": (
        "Haus",
        "noun",
        GrammaticalFeatures(case="Dat", gender="Neut", number="Sing"),
    ),
    "häuser": (
        "Haus",
        "noun",
        GrammaticalFeatures(case="Nom", gender="Neut", number="Plur"),
    ),
    "häusern": (
        "Haus",
        "noun",
        GrammaticalFeatures(case="Dat", gender="Neut", number="Plur"),
    ),
    "kind": (
        "Kind",
        "noun",
        GrammaticalFeatures(case="Nom", gender="Neut", number="Sing"),
    ),
    "kinder": (
        "Kind",
        "noun",
        GrammaticalFeatures(case="Nom", gender="Neut", number="Plur"),
    ),
    "kindern": (
        "Kind",
        "noun",
        GrammaticalFeatures(case="Dat", gender="Neut", number="Plur"),
    ),
    "schnell": (
        "schnell",
        "adjective",
        GrammaticalFeatures(degree="Pos"),
    ),
    "schneller": (
        "schnell",
        "adjective",
        GrammaticalFeatures(degree="Cmp"),
    ),
    "schnellsten": (
        "schnell",
        "adjective",
        GrammaticalFeatures(degree="Sup"),
    ),
    "langsam": (
        "langsam",
        "adjective",
        GrammaticalFeatures(degree="Pos"),
    ),
    "langsamer": (
        "langsam",
        "adjective",
        GrammaticalFeatures(degree="Cmp"),
    ),
    "laufen": (
        "laufen",
        "verb",
        GrammaticalFeatures(verb_form="Inf"),
    ),
    "läuft": (
        "laufen",
        "verb",
        GrammaticalFeatures(person="3", number="Sing", tense="Pres", mood="Ind", verb_form="Fin"),
    ),
    "lief": (
        "laufen",
        "verb",
        GrammaticalFeatures(person="3", number="Sing", tense="Past", mood="Ind", verb_form="Fin"),
    ),
    "gelaufen": (
        "laufen",
        "verb",
        GrammaticalFeatures(verb_form="Part"),
    ),
}


class FixtureMorphologyEngine:
    """Deterministic MorphologyEngine backed by a static table."""

    @property
    def name(self) -> str:
        return _ENGINE_NAME

    def analyze(self, surface: str) -> list[MorphologicalAnalysis]:
        key = normalize(surface)
        entry = _FIXTURE_ENTRIES.get(key)
        if entry is None:
            return []
        lemma, part_of_speech, features = entry
        return [
            make_analysis(
                surface=surface.strip(),
                lemma=lemma,
                part_of_speech=part_of_speech,
                features=features,
                confidence=1.0,
                engine=self.name,
            )
        ]
