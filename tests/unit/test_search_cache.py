"""Unit tests for the search response cache key."""

from __future__ import annotations

from app.services.search.service import cache_key


def test_cache_key_is_case_sensitive() -> None:
    # Query case decides FORM vs NORMALIZED match types, so the two
    # spellings must not share a cache entry.
    assert cache_key("Häusern", 20, "engine") != cache_key("häusern", 20, "engine")


def test_cache_key_is_stable() -> None:
    assert cache_key("gehen", 20, "engine") == cache_key("gehen", 20, "engine")


def test_cache_key_ignores_surrounding_whitespace() -> None:
    assert cache_key("  gehen ", 20, "engine") == cache_key("gehen", 20, "engine")


def test_cache_key_varies_by_limit_and_engine() -> None:
    assert cache_key("gehen", 10, "engine") != cache_key("gehen", 20, "engine")
    assert cache_key("gehen", 20, "fixture") != cache_key("gehen", 20, "spacy")
