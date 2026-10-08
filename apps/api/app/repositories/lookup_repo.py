"""Lookup-index and word-form data access."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.orm import models as orm


class LookupRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def surface_candidates(self, normalized_surface: str) -> list[tuple[orm.Lookup, orm.WordForm]]:
        """Lookup rows for a normalized surface, exact-surface rows first.

        Returns (lookup, word_form) pairs ordered deterministically:
        rows whose surface equals the original query would be sorted by the
        caller; here we order by surface then lookup id.
        """
        stmt = (
            select(orm.Lookup, orm.WordForm)
            .join(orm.WordForm, orm.Lookup.word_form_id == orm.WordForm.id)
            .where(orm.Lookup.normalized_surface == normalized_surface)
            .order_by(orm.WordForm.surface, orm.Lookup.id)
        )
        return [(row[0], row[1]) for row in self._session.execute(stmt)]

    def form_for_lexeme(self, lexeme_id: str, normalized_surface: str) -> orm.WordForm | None:
        stmt = (
            select(orm.WordForm)
            .where(
                orm.WordForm.lexeme_id == lexeme_id,
                orm.WordForm.normalized_surface == normalized_surface,
            )
            .order_by(orm.WordForm.id)
            .limit(1)
        )
        return self._session.scalar(stmt)

    def forms_for_lexemes(self, lexeme_ids: list[str]) -> dict[str, list[orm.WordForm]]:
        if not lexeme_ids:
            return {}
        stmt = (
            select(orm.WordForm)
            .where(orm.WordForm.lexeme_id.in_(lexeme_ids))
            .options(joinedload(orm.WordForm.features))
            .order_by(orm.WordForm.lexeme_id, orm.WordForm.surface, orm.WordForm.id)
        )
        grouped: dict[str, list[orm.WordForm]] = {}
        for row in self._session.scalars(stmt):
            grouped.setdefault(row.lexeme_id, []).append(row)
        return grouped

    def forms_by_surface(
        self, lexeme_ids: list[str], normalized_surface: str
    ) -> dict[str, orm.WordForm]:
        """For each given lexeme, the form whose normalized surface matches."""
        if not lexeme_ids:
            return {}
        stmt = (
            select(orm.WordForm)
            .where(
                orm.WordForm.lexeme_id.in_(lexeme_ids),
                orm.WordForm.normalized_surface == normalized_surface,
            )
            .options(joinedload(orm.WordForm.features))
            .order_by(orm.WordForm.lexeme_id, orm.WordForm.id)
        )
        found: dict[str, orm.WordForm] = {}
        for row in self._session.scalars(stmt):
            found.setdefault(row.lexeme_id, row)
        return found

    def get_form(self, word_form_id: str) -> orm.WordForm | None:
        stmt = (
            select(orm.WordForm)
            .where(orm.WordForm.id == word_form_id)
            .options(joinedload(orm.WordForm.features))
            .limit(1)
        )
        return self._session.scalar(stmt)

    def forms_by_ids(self, word_form_ids: list[str | None]) -> dict[str, orm.WordForm]:
        ids = [form_id for form_id in word_form_ids if form_id]
        if not ids:
            return {}
        stmt = (
            select(orm.WordForm)
            .where(orm.WordForm.id.in_(ids))
            .options(joinedload(orm.WordForm.features))
        )
        return {row.id: row for row in self._session.scalars(stmt)}
