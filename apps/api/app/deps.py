"""FastAPI dependency wiring."""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session
from app.services.cache import ResponseCache
from app.services.morphology_provider import MorphologyEngineProvider
from german_morphology import MorphologyEngine


def get_db() -> Iterator[Session]:
    yield from get_session()


@lru_cache(maxsize=1)
def _morphology_provider_singleton() -> MorphologyEngineProvider:
    """Process-wide provider: the engine is built at most once per worker."""
    settings = get_settings()
    return MorphologyEngineProvider(settings.morphology_engine, spacy_model=settings.spacy_model)


def get_morphology_provider() -> MorphologyEngineProvider:
    return _morphology_provider_singleton()


def get_morphology_engine() -> MorphologyEngine | None:
    return _morphology_provider_singleton().engine


@lru_cache(maxsize=1)
def _response_cache_singleton() -> ResponseCache:
    settings = get_settings()
    return ResponseCache(settings.redis_url, settings.cache_ttl_seconds)


def get_response_cache() -> ResponseCache:
    return _response_cache_singleton()


def reset_dependency_caches() -> None:
    """Test hook: clear cached engine/cache singletons."""
    _response_cache_singleton.cache_clear()
    _morphology_provider_singleton.cache_clear()


SessionDep = Annotated[Session, Depends(get_db)]
MorphologyDep = Annotated[MorphologyEngine | None, Depends(get_morphology_engine)]
MorphologyProviderDep = Annotated[MorphologyEngineProvider, Depends(get_morphology_provider)]
CacheDep = Annotated[ResponseCache, Depends(get_response_cache)]
