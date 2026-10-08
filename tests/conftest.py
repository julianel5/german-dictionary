"""Shared test fixtures.

Environment is configured *before* any application import: an isolated
SQLite database file and the deterministic fixture morphology engine.
No test contacts the network or a live external service.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
_TEST_DB = Path(__file__).resolve().parent / "_tmp" / "test.db"

# --- environment (must run before app imports) --------------------------
os.environ["MORPHOLOGY_ENGINE"] = "fixture"
_TEST_DB.parent.mkdir(parents=True, exist_ok=True)
if _TEST_DB.exists():
    _TEST_DB.unlink()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.as_posix()}"
os.environ.pop("REDIS_URL", None)
os.environ["CACHE_TTL_SECONDS"] = "0"

for _path in (REPO_ROOT, REPO_ROOT / "apps" / "api", REPO_ROOT / "services" / "morphology"):
    _entry = str(_path)
    if _entry not in sys.path:
        sys.path.insert(0, _entry)


@pytest.fixture(scope="session", autouse=True)
def seeded_database() -> Iterator[None]:
    """Create the schema and load the fixture dataset once per run."""
    from app.db import create_all, get_session_factory
    from scripts.dbload import DatabaseLoader
    from scripts.fixtures import load_fixture_dictionary, load_fixture_frequency

    create_all()
    with get_session_factory()() as session:
        loader = DatabaseLoader(session)
        report = loader.load_dictionary(load_fixture_dictionary())
        report.errors.extend(loader.load_frequency(load_fixture_frequency()).errors)
        session.commit()
        assert not report.errors, report.errors
    yield


@pytest.fixture()
def session(seeded_database: None) -> Iterator[object]:
    from app.db import get_session_factory

    db_session = get_session_factory()()
    try:
        yield db_session
    finally:
        db_session.close()


@pytest.fixture(scope="session")
def client(seeded_database: None):  # type: ignore[no-untyped-def]
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
