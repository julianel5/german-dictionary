"""Entry, form and example DTOs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import GrammaticalFeaturesDTO, LexemeDTO


class SenseDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    sense_index: int = Field(alias="senseIndex")
    definition: str
    register: str | None = None
    domain: str | None = None


class WordFormDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    surface: str
    normalized_surface: str = Field(alias="normalizedSurface")
    form_type: str = Field(alias="formType")
    is_searchable: bool = Field(alias="isSearchable")
    features: GrammaticalFeaturesDTO | None = None


class ExampleHighlightDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    word_form_id: str | None = Field(default=None, alias="wordFormId")
    surface: str
    start_offset: int = Field(alias="startOffset")
    end_offset: int = Field(alias="endOffset")


class ExampleSentenceDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    text: str
    translation: str | None = None
    source: str | None = None
    highlights: list[ExampleHighlightDTO] = Field(default_factory=list)


class FrequencyDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    corpus: str
    rank: int
    count: int
    word_form_id: str | None = Field(default=None, alias="wordFormId")


class RelationDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    relation_type: str = Field(alias="relationType")
    lexeme_id: str = Field(alias="lexemeId")
    lemma: str


class EntryDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lexeme: LexemeDTO
    senses: list[SenseDTO] = Field(default_factory=list)
    forms: list[WordFormDTO] = Field(default_factory=list)
    examples: list[ExampleSentenceDTO] = Field(default_factory=list)
    frequency: list[FrequencyDTO] = Field(default_factory=list)
    relations: list[RelationDTO] = Field(default_factory=list)
    principal_forms: list[str] = Field(default_factory=list, alias="principalForms")


class FormsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lexeme_id: str = Field(alias="lexemeId")
    lemma: str
    forms: list[WordFormDTO] = Field(default_factory=list)


class ExamplesResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lexeme_id: str = Field(alias="lexemeId")
    lemma: str
    examples: list[ExampleSentenceDTO] = Field(default_factory=list)
