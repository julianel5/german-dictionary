"""GET /api/search"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.deps import CacheDep, MorphologyProviderDep, SessionDep
from app.schemas.search import SearchResponse
from app.services.search.service import SearchService

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResponse)
def search(
    session: SessionDep,
    provider: MorphologyProviderDep,
    cache: CacheDep,
    q: str = Query(min_length=1, max_length=100, description="Search query"),
    limit: int = Query(default=20, ge=1, le=50, description="Maximum results"),
) -> SearchResponse:
    return SearchService(session, provider, cache).search(q, limit)
