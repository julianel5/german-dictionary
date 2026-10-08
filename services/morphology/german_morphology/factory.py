"""Morphology engine factory.

The application selects an engine at runtime; nothing outside this module
knows which concrete implementation is in use.
"""

from __future__ import annotations

import logging

from german_morphology.fixture_engine import FixtureMorphologyEngine
from german_morphology.types import MorphologyEngine

logger = logging.getLogger(__name__)


def create_morphology_engine(
    engine: str = "auto",
    *,
    spacy_model: str = "de_core_news_sm",
) -> MorphologyEngine | None:
    """Create a morphology engine.

    ``engine`` is one of:

    * ``auto``    - spaCy if the model can be loaded, otherwise no engine
                    (search still resolves known forms through the lookup
                    index; the morphology stage simply yields nothing).
    * ``spacy``   - spaCy engine; raises if the model is unavailable.
    * ``fixture`` - deterministic fixture engine (tests / offline demos).
    * ``none``    - no engine.
    """
    choice = (engine or "auto").strip().lower()
    if choice == "none":
        return None
    if choice == "fixture":
        return FixtureMorphologyEngine()
    if choice == "spacy":
        from german_morphology.spacy_engine import SpacyMorphologyEngine

        return SpacyMorphologyEngine(spacy_model)
    if choice == "auto":
        try:
            from german_morphology.spacy_engine import SpacyMorphologyEngine

            candidate = SpacyMorphologyEngine(spacy_model)
            candidate.analyze("gehen")  # verify the model actually loads
            return candidate
        except Exception as exc:  # pragma: no cover - depends on environment
            logger.warning(
                "spaCy morphology engine unavailable (%s); morphological analysis is disabled",
                exc,
            )
            return None
    raise ValueError(f"Unknown morphology engine: {engine!r}")
