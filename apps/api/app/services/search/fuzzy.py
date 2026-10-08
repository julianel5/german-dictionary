"""Stage 6: fuzzy fallback (pg_trgm / difflib).

Runs only when no other stage matched anything — fuzzy results are never
mixed into higher-confidence matches.
"""

from __future__ import annotations

from app.domain.enums import MatchType
from app.domain.models import SearchCandidate
from app.repositories.search_repos import FuzzySearchRepository
from app.services.search.context import SearchContext


class FuzzyStage:
    name = "fuzzy"

    def __init__(self, fuzzy: FuzzySearchRepository) -> None:
        self._fuzzy = fuzzy

    def run(self, context: SearchContext) -> None:
        if not context.is_empty or not context.normalized:
            return
        for lexeme_id, similarity in self._fuzzy.search(context.normalized, limit=10):
            context.add_candidate(
                SearchCandidate(
                    lexeme_id=lexeme_id,
                    match_type=MatchType.FUZZY,
                    similarity=similarity,
                )
            )
