"""Stage 8: build the API response from ranked candidates."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import MatchType
from app.domain.models import FrequencyInfo, RankedCandidate
from app.orm import models as orm
from app.repositories import mappers
from app.repositories.lookup_repo import LookupRepository
from app.schemas.mappers import features_dto
from app.schemas.search import SearchResponse, SearchResultItem
from app.services.principal_forms import principal_forms
from app.services.search.context import SearchContext

_DEFINITION_LIMIT = 240


def shorten(text: str, limit: int = _DEFINITION_LIMIT) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(",;.") + "…"


class SearchResultBuilder:
    def __init__(self, session: Session, lookups: LookupRepository) -> None:
        self._session = session
        self._lookups = lookups

    def build(
        self,
        context: SearchContext,
        ranked: list[RankedCandidate],
        lexemes: dict[str, orm.Lexeme],
        frequency: dict[str, FrequencyInfo],
    ) -> SearchResponse:
        lexeme_ids = [item.lexeme.id for item in ranked]
        forms_by_lexeme = self._lookups.forms_for_lexemes(lexeme_ids)
        first_senses = self._first_senses(lexeme_ids)
        matched_forms = self._lookups.forms_by_ids([item.candidate.word_form_id for item in ranked])
        lemma_candidates = [
            item.lexeme.id
            for item in ranked
            if item.candidate.word_form_id is None and item.candidate.match_type == MatchType.LEMMA
        ]
        surface_forms = self._lookups.forms_by_surface(lemma_candidates, context.normalized)

        results: list[SearchResultItem] = []
        for item in ranked:
            candidate = item.candidate
            domain_forms = [
                mappers.to_word_form(form) for form in forms_by_lexeme.get(item.lexeme.id, [])
            ]

            matched_row = matched_forms.get(candidate.word_form_id or "")
            if matched_row is None and candidate.match_type == MatchType.LEMMA:
                matched_row = surface_forms.get(item.lexeme.id)
            matched = mappers.to_word_form(matched_row) if matched_row is not None else None

            if matched is not None and matched.features is not None:
                analysis = features_dto(matched.features)
            elif candidate.analysis is not None:
                analysis = features_dto(candidate.analysis.features)
            else:
                analysis = None

            results.append(
                SearchResultItem(
                    lexeme_id=item.lexeme.id,
                    lemma=item.lexeme.lemma,
                    matched_surface=candidate.matched_surface,
                    matched_form_id=matched.id if matched is not None else candidate.word_form_id,
                    part_of_speech=item.lexeme.part_of_speech,
                    frequency_rank=item.frequency_rank,
                    match_type=candidate.match_type,
                    gender=item.lexeme.gender,
                    definition=first_senses.get(item.lexeme.id),
                    principal_forms=principal_forms(item.lexeme, domain_forms),
                    analysis=analysis,
                    morph_certainty=(
                        candidate.morph_certainty
                        if candidate.match_type == MatchType.MORPHOLOGY
                        else None
                    ),
                    score=item.score,
                )
            )

        return SearchResponse(
            query=context.query,
            query_type=results[0].match_type if results else None,
            results=results,
        )

    def _first_senses(self, lexeme_ids: list[str]) -> dict[str, str]:
        if not lexeme_ids:
            return {}
        stmt = (
            select(orm.Sense)
            .where(orm.Sense.lexeme_id.in_(lexeme_ids))
            .order_by(orm.Sense.lexeme_id, orm.Sense.sense_index, orm.Sense.id)
        )
        definitions: dict[str, str] = {}
        for row in self._session.scalars(stmt):
            definitions.setdefault(row.lexeme_id, row.definition)
        return definitions
