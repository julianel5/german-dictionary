"""GET /api/parse"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.deps import MorphologyDep
from app.schemas.parse import ParseResponse
from app.services.parse_service import ParseService

router = APIRouter(tags=["parse"])


@router.get("/parse", response_model=ParseResponse)
def parse(
    engine: MorphologyDep,
    text: str = Query(min_length=1, max_length=1000, description="Text to analyze"),
) -> ParseResponse:
    return ParseService(engine).parse(text)
