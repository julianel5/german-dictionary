"""Shared DTO building blocks."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GrammaticalFeaturesDTO(BaseModel):
    """Structured grammatical features (camelCase on the wire)."""

    model_config = ConfigDict(populate_by_name=True)

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
    extra: dict[str, str] = Field(default_factory=dict)


class LexemeDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    lemma: str
    language: str
    part_of_speech: str = Field(alias="partOfSpeech")
    gender: str | None = None
    register: str | None = None
    domain: str | None = None
