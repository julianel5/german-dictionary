"""Lexeme data access (including the entry aggregate)."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain import models as domain
from app.orm import models as orm
from app.repositories import mappers
from app.repositories.content_repo import ContentRepository


class LexemeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, lexeme_id: str) -> orm.Lexeme | None:
        return self._session.get(orm.Lexeme, lexeme_id)

    def by_ids(self, lexeme_ids: Sequence[str]) -> dict[str, orm.Lexeme]:
        ids = list(dict.fromkeys(lexeme_ids))
        if not ids:
            return {}
        stmt = select(orm.Lexeme).where(orm.Lexeme.id.in_(ids))
        return {row.id: row for row in self._session.scalars(stmt)}

    def by_normalized_lemma(self, normalized_lemma: str, *, limit: int = 10) -> list[orm.Lexeme]:
        stmt = (
            select(orm.Lexeme)
            .where(orm.Lexeme.normalized_lemma == normalized_lemma)
            .order_by(orm.Lexeme.part_of_speech, orm.Lexeme.id)
            .limit(limit)
        )
        return list(self._session.scalars(stmt))

    def lemma_index(self, *, limit: int = 100_000) -> list[orm.Lexeme]:
        """All lexemes, ordered deterministically (SQLite fuzzy fallback)."""
        stmt = select(orm.Lexeme).order_by(orm.Lexeme.normalized_lemma, orm.Lexeme.id).limit(limit)
        return list(self._session.scalars(stmt))

    def aggregate(self, lexeme_id: str) -> domain.LexemeEntry | None:
        stmt = (
            select(orm.Lexeme)
            .where(orm.Lexeme.id == lexeme_id)
            .options(
                selectinload(orm.Lexeme.senses),
                selectinload(orm.Lexeme.word_forms).selectinload(orm.WordForm.features),
                selectinload(orm.Lexeme.frequency_rows),
            )
        )
        row = self._session.scalar(stmt)
        if row is None:
            return None
        content = ContentRepository(self._session)
        lexeme = mappers.to_lexeme(row)
        forms = [mappers.to_word_form(form) for form in row.word_forms]
        examples = content.examples_for_lexeme(lexeme_id)
        relations = content.relations_for_lexeme(lexeme_id)
        return domain.LexemeEntry(
            lexeme=lexeme,
            senses=[mappers.to_sense(sense) for sense in row.senses],
            word_forms=forms,
            examples=examples,
            frequency=[mappers.to_frequency(item) for item in row.frequency_rows],
            relations=relations,
        )
