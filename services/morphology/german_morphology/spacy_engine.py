"""spaCy-based German morphology engine.

Uses the ``de_core_news_sm`` model (German UD-trained pipeline). The model
provides tokenization, POS tags, lemmas and morphological features via
UD-style attributes, which we map onto :class:`GrammaticalFeatures`.
"""

from __future__ import annotations

import logging
import threading

from german_morphology.types import (
    GrammaticalFeatures,
    MorphologicalAnalysis,
    make_analysis,
)

logger = logging.getLogger(__name__)

_POS_MAP: dict[str, str] = {
    "NOUN": "noun",
    "PROPN": "proper_noun",
    "VERB": "verb",
    "AUX": "auxiliary",
    "ADJ": "adjective",
    "ADV": "adverb",
    "PRON": "pronoun",
    "DET": "determiner",
    "ADP": "preposition",
    "CCONJ": "conjunction",
    "SCONJ": "conjunction",
    "NUM": "numeral",
    "PART": "particle",
    "INTJ": "interjection",
    "X": "other",
}

# spaCy German STTS tags that carry adjective-declension information.
_ADJECTIVE_FORM_MAP: dict[str, str] = {
    "ADJA": "attributive",
    "ADJD": "adverbial",
}


class SpacyMorphologyEngine:
    """MorphologyEngine implementation backed by a spaCy German model."""

    def __init__(self, model: str = "de_core_news_sm") -> None:
        self._model = model
        self._nlp = None
        self._lock = threading.Lock()

    @property
    def name(self) -> str:
        return f"spacy:{self._model}"

    def _load(self):  # type: ignore[no-untyped-def]
        if self._nlp is None:
            import spacy

            self._nlp = spacy.load(self._model)
        return self._nlp

    def analyze(self, surface: str) -> list[MorphologicalAnalysis]:
        surface = surface.strip()
        if not surface:
            return []
        with self._lock:
            nlp = self._load()
            doc = nlp(surface)
            analyses: list[MorphologicalAnalysis] = []
            for token in doc:
                if token.is_space or not token.text.strip():
                    continue
                features = _map_features(token)
                analyses.append(
                    make_analysis(
                        surface=token.text,
                        lemma=token.lemma_,
                        part_of_speech=_POS_MAP.get(token.pos_, "other"),
                        features=features,
                        # The sm model exposes no calibrated per-token
                        # probability; report a neutral 1.0 rather than a
                        # fabricated score.
                        confidence=1.0,
                        engine=self.name,
                    )
                )
            return analyses


def _map_features(token) -> GrammaticalFeatures:  # type: ignore[no-untyped-def]
    morph = token.morph.to_dict() if token.morph is not None else {}
    extra = {key: value for key, value in morph.items() if key not in _KNOWN_UD_KEYS}
    adjective_form = _ADJECTIVE_FORM_MAP.get(getattr(token, "tag_", "") or "")
    return GrammaticalFeatures(
        case=morph.get("Case"),
        number=morph.get("Number"),
        gender=morph.get("Gender"),
        person=morph.get("Person"),
        tense=morph.get("Tense"),
        mood=morph.get("Mood"),
        degree=morph.get("Degree"),
        voice=morph.get("Voice"),
        verb_form=morph.get("VerbForm"),
        adjective_form=adjective_form,
        extra=extra,
    )


_KNOWN_UD_KEYS = frozenset(
    {"Case", "Number", "Gender", "Person", "Tense", "Mood", "Degree", "Voice", "VerbForm"}
)
