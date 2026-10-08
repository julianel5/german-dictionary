"""Search request/response DTOs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import MatchType
from app.schemas.common import GrammaticalFeaturesDTO


class SearchResultItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    lexeme_id: str = Field(alias="lexemeId")
    lemma: str
    matched_surface: str | None = Field(default=None, alias="matchedSurface")
    matched_form_id: str | None = Field(default=None, alias="matchedFormId")
    part_of_speech: str = Field(alias="partOfSpeech")
    frequency_rank: int | None = Field(default=None, alias="frequencyRank")
    match_type: MatchType = Field(alias="matchType")
    gender: str | None = None
    definition: str | None = None
    principal_forms: list[str] = Field(default_factory=list, alias="principalForms")
    analysis: GrammaticalFeaturesDTO | None = None
    morph_certainty: float | None = Field(default=None, alias="morphCertainty")
    score: float


class SearchResponse(BaseModel):
    """Search results.

    ``queryType`` is the match type of the top-ranked result and ``None``
    when nothing matched — the API never claims a match kind that did not
    happen.
    """

    model_config = ConfigDict(populate_by_name=True)

    query: str
    query_type: MatchType | None = Field(default=None, alias="queryType")
    results: list[SearchResultItem] = Field(default_factory=list)
    morphology_engine: str | None = Field(default=None, alias="morphologyEngine")
