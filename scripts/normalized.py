"""Normalized, validated records — the contract of the import pipeline.

Raw source data (project fixtures or external files placed under
``data/raw/``) is normalized into these models *before* it ever reaches the
database. Importers for new external sources only need to produce this
shape; the loader downstream stays unchanged.
"""

from __future__ import annotations

import json
import unicodedata
import warnings
from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from app.domain.enums import FormType, Gender, PartOfSpeech, RelationType
from german_morphology import GrammaticalFeatures, normalize

# `register` is a required dictionary field name but also an attribute of
# pydantic's BaseModel; the shadowing warning would be pure noise here.
warnings.filterwarnings(
    "ignore",
    message=r"Field name .* shadows an attribute in parent",
    category=UserWarning,
)

FEATURE_FIELDS = (
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
)


class RecordValidationError(ValueError):
    """Raised when a raw record set fails normalization/validation."""


def _clean(text: str) -> str:
    return unicodedata.normalize("NFC", text.strip())


class NormalizedFeatures(BaseModel):
    """Structured grammatical features as stored on a word form."""

    model_config = ConfigDict(extra="forbid")

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

    def to_domain(self) -> GrammaticalFeatures:
        values = {name: getattr(self, name) for name in FEATURE_FIELDS}
        return GrammaticalFeatures(**values, extra=dict(self.extra))


class NormalizedSense(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sense_index: int = Field(ge=1)
    definition: str
    register: str | None = None
    domain: str | None = None

    @field_validator("definition")
    @classmethod
    def _definition_non_empty(cls, value: str) -> str:
        value = _clean(value)
        if not value:
            raise ValueError("definition must not be empty")
        return value


class NormalizedForm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    surface: str
    form_type: str
    is_searchable: bool = True
    features: NormalizedFeatures | None = None

    @field_validator("surface")
    @classmethod
    def _surface_non_empty(cls, value: str) -> str:
        value = _clean(value)
        if not value:
            raise ValueError("surface must not be empty")
        return value

    @field_validator("form_type")
    @classmethod
    def _form_type_known(cls, value: str) -> str:
        if value not in FormType._value2member_map_:
            raise ValueError(f"unknown form_type {value!r}")
        return value


class NormalizedExampleLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lemma: str
    surface: str

    @field_validator("lemma", "surface")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        value = _clean(value)
        if not value:
            raise ValueError("must not be empty")
        return value


class NormalizedExample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    translation: str | None = None
    source: str | None = None
    linked_forms: list[NormalizedExampleLink] = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def _text_non_empty(cls, value: str) -> str:
        value = _clean(value)
        if not value:
            raise ValueError("text must not be empty")
        return value


class NormalizedRelation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relation_type: str
    target_lemma: str
    target_part_of_speech: str | None = None

    @field_validator("relation_type")
    @classmethod
    def _relation_known(cls, value: str) -> str:
        if value not in RelationType._value2member_map_:
            raise ValueError(f"unknown relation_type {value!r}")
        return value

    @field_validator("target_lemma")
    @classmethod
    def _lemma_non_empty(cls, value: str) -> str:
        value = _clean(value)
        if not value:
            raise ValueError("target_lemma must not be empty")
        return value


class NormalizedLexeme(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lemma: str
    language: str = "de"
    part_of_speech: str
    gender: str | None = None
    register: str | None = None
    domain: str | None = None
    senses: list[NormalizedSense] = Field(min_length=1)
    forms: list[NormalizedForm] = Field(min_length=1)
    relations: list[NormalizedRelation] = Field(default_factory=list)
    examples: list[NormalizedExample] = Field(default_factory=list)

    @field_validator("lemma")
    @classmethod
    def _lemma_non_empty(cls, value: str) -> str:
        value = _clean(value)
        if not value:
            raise ValueError("lemma must not be empty")
        return value

    @field_validator("part_of_speech")
    @classmethod
    def _pos_known(cls, value: str) -> str:
        if value not in PartOfSpeech._value2member_map_:
            raise ValueError(f"unknown part_of_speech {value!r}")
        return value

    @field_validator("gender")
    @classmethod
    def _gender_known(cls, value: str | None) -> str | None:
        if value is not None and value not in Gender._value2member_map_:
            raise ValueError(f"unknown gender {value!r}")
        return value

    @model_validator(mode="after")
    def _unique_senses_and_forms(self) -> NormalizedLexeme:
        indices = [sense.sense_index for sense in self.senses]
        if len(indices) != len(set(indices)):
            raise ValueError(f"duplicate sense_index in lemma {self.lemma!r}")
        surfaces = [normalize(form.surface) for form in self.forms]
        if len(surfaces) != len(set(surfaces)):
            raise ValueError(f"duplicate form surface in lemma {self.lemma!r}")
        return self


class NormalizedDictionary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)
    language: str = "de"
    source: str | None = None
    lexemes: list[NormalizedLexeme] = Field(min_length=1)

    @model_validator(mode="after")
    def _cross_record_references(self) -> NormalizedDictionary:
        keys = [(lex.lemma, lex.part_of_speech) for lex in self.lexemes]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate lemma/part_of_speech pair in dictionary")
        lemmas = {lex.lemma for lex in self.lexemes}
        by_lemma: dict[str, list[NormalizedLexeme]] = {}
        for lex in self.lexemes:
            by_lemma.setdefault(lex.lemma, []).append(lex)

        for lex in self.lexemes:
            for relation in lex.relations:
                if relation.target_lemma not in lemmas:
                    target = relation.target_lemma
                    raise ValueError(f"{lex.lemma!r}: relation target {target!r} not in dictionary")
                if relation.target_part_of_speech is not None:
                    targets = by_lemma[relation.target_lemma]
                    if not any(t.part_of_speech == relation.target_part_of_speech for t in targets):
                        raise ValueError(
                            f"{lex.lemma!r}: relation target {relation.target_lemma!r} "
                            f"with part_of_speech {relation.target_part_of_speech!r} not found"
                        )
            for example in lex.examples:
                for link in example.linked_forms:
                    targets = by_lemma.get(link.lemma, [])
                    if not targets:
                        raise ValueError(
                            f"{lex.lemma!r}: example links unknown lemma {link.lemma!r}"
                        )
                    surfaces = {
                        normalize(form.surface) for target in targets for form in target.forms
                    }
                    if normalize(link.surface) not in surfaces:
                        raise ValueError(
                            f"{lex.lemma!r}: example links unknown form "
                            f"{link.surface!r} of {link.lemma!r}"
                        )
        return self


class NormalizedFrequencyEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lemma: str
    surface: str | None = None
    rank: int = Field(ge=1)
    count: int = Field(ge=0)

    @field_validator("lemma", "surface")
    @classmethod
    def _non_empty(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = _clean(value)
        if not value:
            raise ValueError("must not be empty")
        return value


class NormalizedFrequency(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)
    corpus: str
    source: str | None = None
    entries: list[NormalizedFrequencyEntry] = Field(min_length=1)

    @field_validator("corpus")
    @classmethod
    def _corpus_non_empty(cls, value: str) -> str:
        value = _clean(value)
        if not value:
            raise ValueError("corpus must not be empty")
        return value

    @model_validator(mode="after")
    def _unique_entries(self) -> NormalizedFrequency:
        keys = [(entry.lemma, entry.surface) for entry in self.entries]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate lemma/surface pair in frequency data")
        return self


def _normalize_raw(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Whitespace/NFC cleanup of the raw structure before schema validation."""

    def clean_value(value: Any) -> Any:
        if isinstance(value, str):
            return _clean(value)
        if isinstance(value, list):
            return [clean_value(item) for item in value]
        if isinstance(value, dict):
            return {key: clean_value(item) for key, item in value.items()}
        return value

    return clean_value(dict(raw))


def _ensure_lemma_form(raw_lexemes: list[Any]) -> None:
    """Guarantee a form whose surface equals the lemma exists (form_type=lemma)."""
    for lexeme in raw_lexemes:
        if not isinstance(lexeme, dict):
            continue
        lemma = lexeme.get("lemma")
        forms = lexeme.get("forms")
        if not isinstance(lemma, str) or not isinstance(forms, list):
            continue
        if not any(
            isinstance(form, dict) and str(form.get("surface", "")).strip() == lemma.strip()
            for form in forms
        ):
            forms.append({"surface": lemma, "form_type": "lemma"})


def normalize_dictionary(raw: Mapping[str, Any]) -> NormalizedDictionary:
    """Normalize + validate a raw dictionary structure.

    Raises :class:`RecordValidationError` with a readable message when the
    record set is invalid.
    """
    data = _normalize_raw(raw)
    lexemes = data.get("lexemes")
    if isinstance(lexemes, list):
        _ensure_lemma_form(lexemes)
    try:
        return NormalizedDictionary.model_validate(data)
    except ValidationError as exc:
        raise RecordValidationError(_format_validation_error("dictionary", exc)) from None


def normalize_frequency(raw: Mapping[str, Any]) -> NormalizedFrequency:
    """Normalize + validate a raw frequency structure."""
    data = _normalize_raw(raw)
    try:
        return NormalizedFrequency.model_validate(data)
    except ValidationError as exc:
        raise RecordValidationError(_format_validation_error("frequency", exc)) from None


def _format_validation_error(label: str, exc: ValidationError) -> str:
    lines = [f"invalid {label} data:"]
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"])
        lines.append(f"  - {location}: {error['msg']}")
    return "\n".join(lines)


def dumps(data: NormalizedDictionary | NormalizedFrequency) -> str:
    """Canonical processed-file serialization (deterministic, UTF-8, no escapes)."""
    payload = json.dumps(
        data.model_dump(mode="json"), ensure_ascii=False, indent=2, sort_keys=False
    )
    return payload + "\n"
