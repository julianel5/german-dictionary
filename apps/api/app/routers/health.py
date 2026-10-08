"""GET /api/health"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.deps import CacheDep, MorphologyDep, SessionDep
from app.schemas.parse import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(session: SessionDep, cache: CacheDep, engine: MorphologyDep) -> HealthResponse:
    try:
        session.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        database = "error"
    return HealthResponse(
        status="ok" if database == "ok" else "degraded",
        version=__version__,
        database=database,  # type: ignore[arg-type]
        cache=cache.ping(),
        morphology_engine=engine.name if engine is not None else None,
    )
