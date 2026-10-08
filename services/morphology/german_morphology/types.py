"""Engine-independent morphology types."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from german_morphology.text import normalize


@dataclass(frozen=True, slots=True)
class GrammaticalFeatures:
    """Structured grammatical features.

    Values use short UD-style codes (e.g. ``Case=Nom``, ``Number=Sing``,
    ``Tense=Past``). Fields that do not apply stay ``None``. Rare or
    engine-specific attributes go into ``extra`` so that common features
    remain queryable columns while nothing is lost.
    """

    case: str | None = None
    number: str | None = None
    gender: str | None = None
    person: str | None = None
    tense: str | None = None
    mood: str | None = None
    degree: str | None = None
    voice: str | None = None
    verb_form: str | None = None
    adjective_form: str | None = None
    extra: Mapping[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for name in (
            "case",
            "number",
            "gender",
            "person",
            "tense",
            "mood",
            "degree",
            "voice",
            "verb_form",
            "adjective_form",
        ):
            value = getattr(self, name)
            if value is not None:
                data[name] = value
        data.update(self.extra)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> GrammaticalFeatures:
        if not data:
            return cls()
        known = {
            "case",
            "number",
            "gender",
            "person",
            "tense",
            "mood",
            "degree",
            "voice",
            "verb_form",
            "adjective_form",
        }
        kwargs = {key: data[key] for key in known if key in data and data[key] is not None}
        extra = {key: str(value) for key, value in data.items() if key not in known}
        return cls(extra=extra, **kwargs)


@dataclass(frozen=True, slots=True)
class MorphologicalAnalysis:
    """One possible morphological analysis of a surface string."""

    surface: str
    lemma: str
    normalized_lemma: str
    part_of_speech: str | None
    features: GrammaticalFeatures
    confidence: float
    engine: str


@runtime_checkable
class MorphologyEngine(Protocol):
    """Analyze German surface forms into lemma + grammatical features."""

    @property
    def name(self) -> str: ...

    def analyze(self, surface: str) -> list[MorphologicalAnalysis]: ...


def make_analysis(
    *,
    surface: str,
    lemma: str,
    part_of_speech: str | None,
    features: GrammaticalFeatures,
    confidence: float,
    engine: str,
) -> MorphologicalAnalysis:
    return MorphologicalAnalysis(
        surface=surface,
        lemma=lemma,
        normalized_lemma=normalize(lemma),
        part_of_speech=part_of_speech,
        features=features,
        confidence=confidence,
        engine=engine,
    )
