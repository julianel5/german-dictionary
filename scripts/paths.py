"""Make the monorepo's Python packages importable without an editable install.

Entry points (``python -m scripts.seed`` etc.) are normally run from the
repository root, where ``scripts`` is importable but ``app`` (apps/api) and
``german_morphology`` (services/morphology) are not. Every entry point calls
:func:`ensure_paths` first, so the repository works both from a fresh clone
(and ``pip install -e .``) alike.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
API_PACKAGE = REPO_ROOT / "apps" / "api"
MORPHOLOGY_PACKAGE = REPO_ROOT / "services" / "morphology"


def ensure_paths() -> None:
    """Prepend the repo root and the two vendored packages to ``sys.path``."""
    for path in (REPO_ROOT, API_PACKAGE, MORPHOLOGY_PACKAGE):
        entry = str(path)
        if entry not in sys.path:
            sys.path.insert(0, entry)
