"""Load the bundled fixture dataset (data/fixtures/).

The fixture set makes the whole application runnable without downloading
any external data: seed, tests and the Docker image all use it.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from scripts.normalized import (
    NormalizedDictionary,
    NormalizedFrequency,
    normalize_dictionary,
    normalize_frequency,
)

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "data" / "fixtures"
DICTIONARY_FIXTURE = FIXTURE_DIR / "dictionary.json"
FREQUENCY_FIXTURE = FIXTURE_DIR / "frequency.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"fixture file not found: {path}")
    with path.open(encoding="utf-8") as handle:
        data: dict[str, Any] = json.load(handle)
    return data


@lru_cache(maxsize=1)
def load_fixture_dictionary() -> NormalizedDictionary:
    return normalize_dictionary(read_json(DICTIONARY_FIXTURE))


@lru_cache(maxsize=1)
def load_fixture_frequency() -> NormalizedFrequency:
    return normalize_frequency(read_json(FREQUENCY_FIXTURE))
