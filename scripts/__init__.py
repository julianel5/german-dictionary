"""Developer-facing entry points: seed, importers, maintenance, API runner."""

from __future__ import annotations

__all__ = ["paths"]

from scripts import paths

paths.ensure_paths()
