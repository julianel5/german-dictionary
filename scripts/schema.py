"""Schema management helpers for scripts (seed, importers, maintenance).

Prefers versioned Alembic migrations when available and falls back to
``Base.metadata.create_all`` (identical DDL, generated from the same
models) so a fresh clone always works.
"""

from __future__ import annotations

import logging
from pathlib import Path

from scripts.paths import API_PACKAGE, REPO_ROOT

logger = logging.getLogger(__name__)

ALEMBIC_INI_CANDIDATES = (
    API_PACKAGE / "alembic.ini",
    REPO_ROOT / "alembic.ini",
)


def find_alembic_ini() -> Path | None:
    for candidate in ALEMBIC_INI_CANDIDATES:
        if candidate.is_file():
            return candidate
    return None


def ensure_schema() -> str:
    """Create/upgrade the database schema. Returns the method used."""
    from app.db import create_all

    ini = find_alembic_ini()
    if ini is not None:
        try:
            from alembic import command
            from alembic.config import Config

            config = Config(str(ini))
            config.set_main_option("script_location", str(ini.parent / "alembic"))
            command.upgrade(config, "head")
            return "alembic"
        except Exception as exc:  # pragma: no cover - depends on environment
            logger.warning("alembic upgrade failed (%s); falling back to create_all", exc)
    create_all()
    return "create_all"
