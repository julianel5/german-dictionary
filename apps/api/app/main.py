"""FastAPI application factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import get_settings
from app.routers import entries, forms, health, parse, search

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Idempotent: Alembic (via scripts) owns migrations; create_all only
    # fills in missing tables so a fresh clone can boot immediately.
    try:
        from app.db import create_all

        create_all()
    except Exception as exc:  # pragma: no cover - depends on environment
        logger.warning("could not ensure schema at startup: %s", exc)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="German Dictionary API",
        version=__version__,
        description="Search, entries, forms and morphological parsing.",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    for router in (health.router, search.router, entries.router, forms.router, parse.router):
        application.include_router(router, prefix="/api")
    return application


app = create_app()
