"""Stage 1: normalize the query."""

from __future__ import annotations

from app.services.search.context import SearchContext
from german_morphology import normalize


class NormalizeStage:
    name = "normalize"

    def run(self, context: SearchContext) -> None:
        context.normalized = normalize(context.query)
