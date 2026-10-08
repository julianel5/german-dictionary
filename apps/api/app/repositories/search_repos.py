"""Dialect-aware definition and fuzzy search backends.

Definition search is a deliberate, documented relevance policy rather
than raw full-text search:

* only the **leading gloss** of a definition is searchable — the text
  before the first `` — `` (em-dash) separator. Fixture/import senses
  carry an English translation gloss first, then a German explanation;
  matching the explanation is what produced noisy results such as
  ``funktionieren -> gehen``.
* the query must match a **whole word** (Unicode-aware, case-insensitive),
  not an arbitrary substring.
* results are ordered deterministically by ``(lexeme_id, sense_index)`` on
  both dialects.

Fuzzy search keeps its backends: ``pg_trgm`` similarity on PostgreSQL,
``difflib`` on SQLite.
"""

from __future__ import annotations

import difflib
import logging
import re

from sqlalchemy import case, func, select
from sqlalchemy.exc import InvalidRequestError, OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.orm import models as orm

logger = logging.getLogger(__name__)

#: pg_trgm similarity threshold / difflib cutoff (different scales).
_PG_TRGM_THRESHOLD = 0.3
_DIFFLIB_CUTOFF = 0.55

_SAFE_ESCAPE = str.maketrans({"%": r"\%", "_": r"\_"})

#: Separates the searchable English gloss from the German explanation.
_GLOSS_SEPARATOR = " — "

#: One-character definition queries match far too much to be meaningful.
_MIN_DEFINITION_QUERY_LENGTH = 2


def leading_gloss(definition: str) -> str:
    """Return the searchable part of a definition (text before `` — ``).

    Definitions without the separator are treated as an all-gloss string.
    """
    head, separator, _explanation = definition.partition(_GLOSS_SEPARATOR)
    return head if separator else definition


def matches_gloss(definition: str, query: str) -> bool:
    """Whether ``query`` occurs as a whole word in the definition's gloss."""
    query = query.strip()
    if len(query) < _MIN_DEFINITION_QUERY_LENGTH:
        return False
    pattern = re.compile(rf"(?<!\w){re.escape(query)}(?!\w)", re.IGNORECASE)
    return pattern.search(leading_gloss(definition)) is not None


class DefinitionSearchRepository:
    """Whole-word search over the leading gloss of each sense definition."""

    def __init__(self, session: Session) -> None:
        self._session = session
        bind = session.get_bind()
        self._dialect = bind.dialect.name if bind is not None else "sqlite"
        self._gloss = self._gloss_expression()

    def search(self, query: str, *, limit: int = 20) -> list[orm.Sense]:
        query = query.strip()
        if len(query) < _MIN_DEFINITION_QUERY_LENGTH:
            return []

        # SQL prefilters to glosses containing the query as a substring
        # (case-insensitively); the whole-word policy is enforced in Python
        # so both dialects return the same set.
        pattern = f"%{query.translate(_SAFE_ESCAPE)}%"
        stmt = (
            select(orm.Sense)
            .where(self._gloss.ilike(pattern, escape="\\"))
            .order_by(orm.Sense.lexeme_id, orm.Sense.sense_index)
            .limit(limit)
        )
        rows = list(self._session.scalars(stmt))
        return [row for row in rows if matches_gloss(row.definition, query)][:limit]

    def _gloss_expression(self):  # type: ignore[no-untyped-def]
        """SQL expression yielding the leading gloss, per dialect."""
        definition = orm.Sense.definition
        if self._dialect == "postgresql":
            return func.split_part(definition, _GLOSS_SEPARATOR, 1)
        position = func.instr(definition, _GLOSS_SEPARATOR)
        return case(
            (position > 0, func.substr(definition, 1, position - 1)),
            else_=definition,
        )


class FuzzySearchRepository:
    """Approximate lemma matching (fallback stage, runs only when nothing else matched)."""

    def __init__(self, session: Session) -> None:
        self._session = session
        bind = session.get_bind()
        self._dialect = bind.dialect.name if bind is not None else "sqlite"

    def search(self, query: str, *, limit: int = 10) -> list[tuple[str, float]]:
        """Return (lexeme_id, similarity) pairs, best first."""
        query = query.strip()
        if not query:
            return []
        if self._dialect == "postgresql":
            try:
                return self._search_trgm(query, limit)
            except (ProgrammingError, OperationalError, InvalidRequestError):
                self._session.rollback()
                logger.warning("pg_trgm similarity failed; falling back to difflib")
        return self._search_difflib(query, limit)

    def _search_trgm(self, query: str, limit: int) -> list[tuple[str, float]]:
        similarity = func.similarity(orm.Lexeme.normalized_lemma, query)
        stmt = (
            select(orm.Lexeme.id, similarity.label("similarity"))
            .where(similarity >= _PG_TRGM_THRESHOLD)
            .order_by(similarity.desc(), orm.Lexeme.normalized_lemma, orm.Lexeme.id)
            .limit(limit)
        )
        return [(row.id, float(row.similarity)) for row in self._session.execute(stmt)]

    def _search_difflib(self, query: str, limit: int) -> list[tuple[str, float]]:
        rows = self._session.execute(
            select(orm.Lexeme.id, orm.Lexeme.normalized_lemma).order_by(
                orm.Lexeme.normalized_lemma, orm.Lexeme.id
            )
        )
        candidates = [(lexeme_id, lemma) for lexeme_id, lemma in rows]
        matcher = difflib.SequenceMatcher(a=query, b="")
        scored: list[tuple[str, float]] = []
        for lexeme_id, lemma in candidates:
            matcher.set_seq2(lemma)
            ratio = matcher.ratio()
            if ratio >= _DIFFLIB_CUTOFF:
                scored.append((lexeme_id, ratio))
        scored.sort(key=lambda item: (-item[1], item[0]))
        return scored[:limit]
