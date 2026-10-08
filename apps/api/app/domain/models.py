"""Domain models.

These are plain dataclasses, independent from SQLAlchemy ORM rows and from
API (Pydantic) DTOs. Services translate between all three layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.enums import MatchType, RelationType
from german_morphology import GrammaticalFeatures, MorphologicalAnalysis


@dataclass(slots=True)
class Lexeme:
    id: str
    lemma: str
    normalized_lemma: str
    language: str
    part_of_speech: str
    gender: str | None = None
    register: str | None = None
    domain: str | None = None


@dataclass(slots=True)
class Sense:
    id: str
    sense_index: int
    definition: str
    register: str | None = None
    domain: str | None = None


@dataclass(slots=True)
class WordForm:
    id: str
    lexeme_id: str
    surface: str
    normalized_surface: str
    form_type: str
    is_searchable: bool = True
    features: GrammaticalFeatures | None = None


@dataclass(slots=True)
class LookupMatch:
    lexeme_id: str
    word_form_id: str
    surface: str
    is_exact: bool


@dataclass(slots=True)
class FrequencyInfo:
    corpus: str
    rank: int
    count: int
    word_form_id: str | None = None


@dataclass(slots=True)
class ExampleSentence:
    id: str
    text: str
    translation: str | None = None
    source: str | None = None
    word_form_id: str | None = None
    start_offset: int | None = None
    end_offset: int | None = None


@dataclass(slots=True)
class LexicalRelationLink:
    relation_type: RelationType
    target_lexeme_id: str
    target_lemma: str


@dataclass(slots=True)
class SearchCandidate:
    lexeme_id: str
    match_type: MatchType
    matched_surface: str | None = None
    word_form_id: str | None = None
    morph_certainty: float = 1.0
    similarity: float = 0.0
    analysis: MorphologicalAnalysis | None = None


@dataclass(slots=True)
class RankedCandidate:
    candidate: SearchCandidate
    lexeme: Lexeme
    frequency_rank: int | None = None
    score: float = 0.0


@dataclass(slots=True)
class LexemeEntry:
    """Full aggregate for a dictionary entry."""

    lexeme: Lexeme
    senses: list[Sense] = field(default_factory=list)
    word_forms: list[WordForm] = field(default_factory=list)
    examples: list[ExampleSentence] = field(default_factory=list)
    frequency: list[FrequencyInfo] = field(default_factory=list)
    relations: list[LexicalRelationLink] = field(default_factory=list)
