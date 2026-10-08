"""Parse and health DTOs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import GrammaticalFeaturesDTO


class ParseAnalysisDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lemma: str
    part_of_speech: str | None = Field(default=None, alias="partOfSpeech")
    features: GrammaticalFeaturesDTO
    confidence: float
    engine: str


class ParseTokenDTO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    surface: str
    start: int
    end: int
    analyses: list[ParseAnalysisDTO] = Field(default_factory=list)


class ParseResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    text: str
    engine: str | None = None
    tokens: list[ParseTokenDTO] = Field(default_factory=list)


class HealthResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: Literal["ok", "degraded"]
    version: str
    database: Literal["ok", "error"]
    cache: bool
    morphology_engine: str | None = Field(default=None, alias="morphologyEngine")
