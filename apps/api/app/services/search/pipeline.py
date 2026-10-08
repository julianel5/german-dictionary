"""Pipeline wiring and execution."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.models import FrequencyInfo
from app.repositories.content_repo import ContentRepository
from app.repositories.lexeme_repo import LexemeRepository
from app.repositories.lookup_repo import LookupRepository
from app.repositories.search_repos import DefinitionSearchRepository, FuzzySearchRepository
from app.schemas.search import SearchResponse
from app.services.search.builder import SearchResultBuilder
from app.services.search.context import SearchContext, SearchStage
from app.services.search.definition import DefinitionStage
from app.services.search.fuzzy import FuzzyStage
from app.services.search.lemma import ExactLemmaStage
from app.services.search.morphology_stage import MorphologyStage
from app.services.search.normalize import NormalizeStage
from app.services.search.ranking import SearchRanker
from app.services.search.surface import ExactSurfaceStage
from german_morphology import MorphologyEngine


class SearchPipeline:
    """Runs the stages in order, then ranks and builds the response.

    1. normalize -> 2. exact surface -> 3. exact lemma -> 4. morphology ->
    5. definition -> 6. fuzzy (fallback) -> 7. rank -> 8. build response.
    """

    def __init__(
        self,
        *,
        stages: list[SearchStage],
        ranker: SearchRanker,
        builder: SearchResultBuilder,
        lexemes: LexemeRepository,
        content: ContentRepository,
        engine_name: str | None = None,
    ) -> None:
        self.stages = stages
        self.ranker = ranker
        self.builder = builder
        self.lexemes = lexemes
        self.content = content
        self.engine_name = engine_name

    def execute(self, query: str, limit: int = 20) -> SearchResponse:
        context = SearchContext(query=query, limit=limit)
        for stage in self.stages:
            stage.run(context)

        lexeme_ids = list(context.candidates)
        lexeme_rows = self.lexemes.by_ids(lexeme_ids)
        frequency: dict[str, FrequencyInfo] = self.content.best_frequency(lexeme_ids)

        ranked = self.ranker.rank(context, lexeme_rows, frequency)
        response = self.builder.build(context, ranked, lexeme_rows, frequency)
        response.morphology_engine = self.engine_name
        return response


def build_search_pipeline(session: Session, engine: MorphologyEngine | None) -> SearchPipeline:
    """Default wiring. Swapping the engine swaps the morphology stage only."""
    lexemes = LexemeRepository(session)
    lookups = LookupRepository(session)
    content = ContentRepository(session)
    stages: list[SearchStage] = [
        NormalizeStage(),
        ExactSurfaceStage(lookups),
        ExactLemmaStage(lexemes),
        MorphologyStage(engine, lexemes, lookups),
        DefinitionStage(DefinitionSearchRepository(session)),
        FuzzyStage(FuzzySearchRepository(session)),
    ]
    return SearchPipeline(
        stages=stages,
        ranker=SearchRanker(),
        builder=SearchResultBuilder(session, lookups),
        lexemes=lexemes,
        content=content,
        engine_name=engine.name if engine is not None else None,
    )
