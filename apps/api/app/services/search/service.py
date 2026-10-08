"""Search service: cache wrapper around the staged pipeline."""

from __future__ import annotations

import hashlib
import logging

from sqlalchemy.orm import Session

from app.schemas.search import SearchResponse
from app.services.cache import ResponseCache
from app.services.morphology_provider import MorphologyEngineProvider
from app.services.search.pipeline import build_search_pipeline

logger = logging.getLogger(__name__)

#: Bumped when search semantics change, so stale cache entries are ignored.
_CACHE_VERSION = "v2"


def cache_key(query: str, limit: int, engine_name: str) -> str:
    """Cache key for a search request.

    The key is case-sensitive: query case is part of the response
    contract (it decides ``FORM`` vs ``NORMALIZED`` match types), so
    ``Häusern`` and ``häusern`` must never share a cache entry.
    """
    digest = hashlib.sha256(query.strip().encode("utf-8")).hexdigest()[:16]
    return f"search|{_CACHE_VERSION}|{digest}|{limit}|{engine_name}"


class SearchService:
    def __init__(
        self,
        session: Session,
        provider: MorphologyEngineProvider,
        cache: ResponseCache | None = None,
    ) -> None:
        self._session = session
        self._provider = provider
        self._cache = cache

    def search(self, query: str, limit: int = 20) -> SearchResponse:
        # The cache token is derived from configuration only, so a cache
        # hit never forces the (potentially expensive) engine to be built.
        key = cache_key(query, limit, self._provider.cache_token)
        if self._cache is not None:
            cached = self._cache.get(key)
            if cached is not None:
                try:
                    return SearchResponse.model_validate_json(cached)
                except Exception:  # pragma: no cover - corrupt cache entries
                    logger.warning("discarding invalid cached search response")

        engine = self._provider.engine  # built at most once per process
        pipeline = build_search_pipeline(self._session, engine)
        response = pipeline.execute(query, limit)

        if self._cache is not None and response.results:
            self._cache.set(key, response.model_dump_json())
        return response
