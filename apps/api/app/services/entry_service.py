"""Entry detail service (aggregate -> DTOs)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.models import LexemeEntry
from app.repositories import mappers
from app.repositories.lexeme_repo import LexemeRepository
from app.repositories.lookup_repo import LookupRepository
from app.schemas.entries import (
    EntryDetailResponse,
    ExamplesResponse,
    FormsResponse,
    WordFormDTO,
)
from app.schemas.mappers import (
    example_dto,
    frequency_dto,
    lexeme_dto,
    relation_dto,
    sense_dto,
    word_form_dto,
)
from app.services.principal_forms import principal_forms


class EntryNotFoundError(LookupError):
    """Raised when a lexeme or word form id does not exist."""


class EntryService:
    def __init__(self, session: Session) -> None:
        self._lexemes = LexemeRepository(session)
        self._lookups = LookupRepository(session)

    def entry(self, lexeme_id: str) -> EntryDetailResponse:
        aggregate = self._lexemes.aggregate(lexeme_id)
        if aggregate is None:
            raise EntryNotFoundError(lexeme_id)
        return self._to_detail(aggregate)

    def forms(self, lexeme_id: str) -> FormsResponse:
        aggregate = self._lexemes.aggregate(lexeme_id)
        if aggregate is None:
            raise EntryNotFoundError(lexeme_id)
        return FormsResponse(
            lexeme_id=aggregate.lexeme.id,
            lemma=aggregate.lexeme.lemma,
            forms=[word_form_dto(form) for form in aggregate.word_forms],
        )

    def examples(self, lexeme_id: str) -> ExamplesResponse:
        aggregate = self._lexemes.aggregate(lexeme_id)
        if aggregate is None:
            raise EntryNotFoundError(lexeme_id)
        return ExamplesResponse(
            lexeme_id=aggregate.lexeme.id,
            lemma=aggregate.lexeme.lemma,
            examples=[example_dto(example) for example in aggregate.examples],
        )

    def form(self, word_form_id: str) -> WordFormDTO:
        row = self._lookups.get_form(word_form_id)
        if row is None:
            raise EntryNotFoundError(word_form_id)
        return word_form_dto(mappers.to_word_form(row))

    @staticmethod
    def _to_detail(aggregate: LexemeEntry) -> EntryDetailResponse:
        return EntryDetailResponse(
            lexeme=lexeme_dto(aggregate.lexeme),
            senses=[sense_dto(sense) for sense in aggregate.senses],
            forms=[word_form_dto(form) for form in aggregate.word_forms],
            examples=[example_dto(example) for example in aggregate.examples],
            frequency=[frequency_dto(item) for item in aggregate.frequency],
            relations=[relation_dto(link) for link in aggregate.relations],
            principal_forms=principal_forms(aggregate.lexeme, aggregate.word_forms),
        )
