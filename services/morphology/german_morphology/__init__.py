"""German morphology abstraction.

The rest of the application depends only on the :class:`MorphologyEngine`
protocol and the data types in this module. Concrete engines (spaCy-based,
fixture-based, future implementations) are created through the factory in
:mod:`german_morphology.factory`.
"""

from german_morphology.factory import create_morphology_engine
from german_morphology.text import normalize
from german_morphology.types import (
    GrammaticalFeatures,
    MorphologicalAnalysis,
    MorphologyEngine,
)

__all__ = [
    "GrammaticalFeatures",
    "MorphologicalAnalysis",
    "MorphologyEngine",
    "create_morphology_engine",
    "normalize",
]
