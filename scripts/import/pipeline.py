"""Import pipeline: raw -> normalize -> validate -> processed -> PostgreSQL.

Raw source files (``data/raw/``) are opened read-only and never modified.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.normalized import (
    NormalizedDictionary,
    NormalizedFrequency,
    dumps,
    normalize_dictionary,
    normalize_frequency,
)


def read_raw(path: Path) -> dict[str, Any]:
    """Read a raw source file (read-only; the file is never modified)."""
    if not path.is_file():
        raise FileNotFoundError(
            f"raw source file not found: {path}\n"
            "Place the source file under data/raw/ (see data/raw/README.md)."
        )
    with path.open(encoding="utf-8") as handle:
        data: dict[str, Any] = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return data


def write_processed(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def process_dictionary(raw_path: Path, processed_path: Path) -> NormalizedDictionary:
    """raw -> normalized/validated -> processed representation."""
    data = normalize_dictionary(read_raw(raw_path))
    write_processed(processed_path, dumps(data))
    return data


def process_frequency(raw_path: Path, processed_path: Path) -> NormalizedFrequency:
    """raw -> normalized/validated -> processed representation."""
    data = normalize_frequency(read_raw(raw_path))
    write_processed(processed_path, dumps(data))
    return data
