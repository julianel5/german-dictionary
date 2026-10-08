"""Stage 3: exact lemma lookup (normalized comparison)."""

from __future__ import annotations

from app.domain.enums import MatchType
from app.domain.models import SearchCandidate
from app.repositories.lexeme_repo import LexemeRepository
from app.services.search.context import SearchContext


class ExactLemmaStage:
    name = "exact_lemma"

    def __init__(self, lexemes: LexemeRepository) -> None:
        self._lexemes = lexemes

    def run(self, context: SearchContext) -> None:
        if not context.normalized:
            return
        for lexeme in self._lexemes.by_normalized_lemma(context.normalized):
            context.add_candidate(
                SearchCandidate(
                    lexeme_id=lexeme.id,
                    match_type=MatchType.LEMMA,
                    matched_surface=lexeme.lemma,
                )
            )
