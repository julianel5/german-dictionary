"""Stage 5: definition search over the leading gloss (whole-word).

Runs only when stages 1-4 produced no candidates, mirroring the fuzzy
stage: definitions must never pollute an exact lemma/form/normalized or
morphology match.
"""

from __future__ import annotations

from app.domain.enums import MatchType
from app.domain.models import SearchCandidate
from app.repositories.search_repos import DefinitionSearchRepository
from app.services.search.context import SearchContext


class DefinitionStage:
    name = "definition"

    def __init__(self, definitions: DefinitionSearchRepository) -> None:
        self._definitions = definitions

    def run(self, context: SearchContext) -> None:
        if not context.is_empty:
            return
        for sense in self._definitions.search(context.query, limit=20):
            context.add_candidate(
                SearchCandidate(
                    lexeme_id=sense.lexeme_id,
                    match_type=MatchType.DEFINITION,
                )
            )
