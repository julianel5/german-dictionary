"""Stage 2: exact surface lookup through the lookup index.

Classifies each hit honestly:

* ``FORM``       - stored surface equals the query string exactly
* ``NORMALIZED`` - stored surface equals the query only after normalization
"""

from __future__ import annotations

from app.domain.enums import MatchType
from app.domain.models import SearchCandidate
from app.repositories.lookup_repo import LookupRepository
from app.services.search.context import SearchContext


class ExactSurfaceStage:
    name = "exact_surface"

    def __init__(self, lookups: LookupRepository) -> None:
        self._lookups = lookups

    def run(self, context: SearchContext) -> None:
        if not context.normalized:
            return
        rows = self._lookups.surface_candidates(context.normalized)
        # Stable sort: exact-surface rows first, SQL order preserved.
        rows.sort(key=lambda pair: 0 if pair[1].surface == context.query else 1)
        for lookup, form in rows:
            match_type = MatchType.FORM if form.surface == context.query else MatchType.NORMALIZED
            context.add_candidate(
                SearchCandidate(
                    lexeme_id=lookup.lexeme_id,
                    match_type=match_type,
                    matched_surface=form.surface,
                    word_form_id=form.id,
                )
            )
