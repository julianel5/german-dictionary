"""Lazy, process-wide morphology engine provider.

Constructing a morphology engine can be expensive: in ``auto``/``spacy``
mode the factory loads the spaCy German model (roughly a second per
load). The API must therefore build the engine at most once per worker
and must not build it at all when a request is served from the response
cache.

The provider separates two concerns:

* :attr:`cache_token` — a cheap, configuration-derived identifier used in
  the search cache key. It never constructs an engine.
* :attr:`engine` — the resolved engine (or ``None``), built lazily on
  first use and memoised for the lifetime of the process.

Resolution is guarded by a lock so concurrent requests cannot race into
building two engines. The resolved engine is immutable afterwards, so it
is safe to share across requests.
"""

from __future__ import annotations

import threading
from collections.abc import Callable

from german_morphology import MorphologyEngine, create_morphology_engine

#: Sentinel-less default: ``None`` means "use the real factory".
EngineFactory = Callable[[], "MorphologyEngine | None"]


class MorphologyEngineProvider:
    """Defers engine construction while exposing a cheap cache token."""

    def __init__(
        self,
        engine: str = "auto",
        *,
        spacy_model: str = "de_core_news_sm",
        factory: EngineFactory | None = None,
    ) -> None:
        self._engine_setting = engine
        self._spacy_model = spacy_model
        self._factory = factory
        self._engine: MorphologyEngine | None = None
        self._resolved = False
        self._lock = threading.Lock()

    @property
    def cache_token(self) -> str:
        """Cheap, stable identifier for the configured engine.

        Deliberately derived from configuration only — never from the
        resolved engine — so a cache lookup does not trigger construction.
        ``auto`` resolves to spaCy or ``none`` at runtime, but the token
        only needs to be stable within a process for its configuration.
        """
        choice = (self._engine_setting or "auto").strip().lower()
        if choice in {"auto", "spacy"}:
            return f"{choice}:{self._spacy_model}"
        return choice

    def _create(self) -> MorphologyEngine | None:
        if self._factory is not None:
            return self._factory()
        return create_morphology_engine(self._engine_setting, spacy_model=self._spacy_model)

    @property
    def engine(self) -> MorphologyEngine | None:
        """The engine, built at most once (thread-safe, lazy)."""
        if not self._resolved:
            with self._lock:
                if not self._resolved:
                    self._engine = self._create()
                    self._resolved = True
        return self._engine

    @property
    def engine_name(self) -> str | None:
        engine = self.engine
        return engine.name if engine is not None else None
