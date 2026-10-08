"""Unit tests for the lazy, process-wide morphology engine provider.

These tests never load spaCy: engine construction is injected, and the
provider's job is only to build lazily and exactly once.
"""

from __future__ import annotations

from app.services.morphology_provider import MorphologyEngineProvider


class _FakeEngine:
    def __init__(self, name: str) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def analyze(self, surface: str):  # type: ignore[no-untyped-def]
        return []


def test_cache_token_is_cheap_and_does_not_build_engine() -> None:
    calls: list[int] = []

    def factory() -> _FakeEngine:
        calls.append(1)
        return _FakeEngine("fake")

    provider = MorphologyEngineProvider("spacy", factory=factory)
    assert provider.cache_token == "spacy:de_core_news_sm"
    assert calls == []  # computing the key must not construct the engine


def test_engine_is_resolved_repeatedly_to_the_same_instance() -> None:
    calls: list[int] = []

    def factory() -> _FakeEngine:
        calls.append(1)
        return _FakeEngine("fake")

    provider = MorphologyEngineProvider("auto", factory=factory)
    first = provider.engine
    second = provider.engine
    assert first is second
    assert len(calls) == 1  # built once, reused thereafter
    assert provider.engine_name == "fake"


def test_cache_token_tracks_configuration() -> None:
    assert MorphologyEngineProvider("none").cache_token == "none"
    assert MorphologyEngineProvider("fixture").cache_token == "fixture"
    assert MorphologyEngineProvider("auto", spacy_model="m").cache_token == "auto:m"
    assert MorphologyEngineProvider("spacy", spacy_model="m").cache_token == "spacy:m"


def test_none_engine_resolves_to_none() -> None:
    provider = MorphologyEngineProvider("none", factory=lambda: None)
    assert provider.engine is None
    assert provider.engine_name is None


def test_process_wide_dependency_reuses_one_engine() -> None:
    from app import deps

    deps.reset_dependency_caches()
    try:
        assert deps.get_morphology_engine() is deps.get_morphology_engine()
        assert deps.get_morphology_provider() is deps.get_morphology_provider()
    finally:
        deps.reset_dependency_caches()


def test_cache_hit_does_not_resolve_engine(session) -> None:  # type: ignore[no-untyped-def]
    from app.services.search.service import SearchService

    resolved: list[int] = []

    def factory() -> _FakeEngine:
        resolved.append(1)
        return _FakeEngine("fake")

    provider = MorphologyEngineProvider("fixture", factory=factory)

    class _HitCache:
        def get(self, key: str) -> str:
            return (
                '{"query": "gehen", "query_type": null, "morphology_engine": null, "results": []}'
            )

        def set(self, key: str, value: str) -> None:  # pragma: no cover - never hit
            raise AssertionError("cache must not be written on a hit")

    response = SearchService(session, provider, _HitCache()).search("gehen")
    assert response.query == "gehen"
    assert resolved == []  # a cache hit never builds the engine
