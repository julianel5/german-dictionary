"""Alembic environment: metadata from the SQLAlchemy models, URL from
DATABASE_URL (or the ini file when explicitly set)."""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

_API_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = _API_DIR.parents[1]
for _path in (_REPO_ROOT, _API_DIR, _REPO_ROOT / "services" / "morphology"):
    _entry = str(_path)
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

from app.config import get_settings  # noqa: E402
from app.orm.models import Base  # noqa: E402

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    url = config.get_main_option("sqlalchemy.url")
    return url if url else get_settings().effective_database_url


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        url=_database_url(),
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
