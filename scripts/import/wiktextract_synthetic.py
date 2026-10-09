"""Synthetic Wiktextract importer (safe mode only).

This importer operates on synthetic data only. Real-data imports are
BLOCKED by default via environment/config flag. It preserves homonyms,
nullable sense_id for translations, deterministic keys when external_id
is missing, and produces provenance-aware normalized structures.

Do not use with real dumps until L1/L4 gates are satisfied.
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


REAL_IMPORT_ALLOWED = os.getenv("ALLOW_REAL_WIKTEXTRACT_IMPORT", "false").lower() in (
    "1",
    "true",
    "yes",
)


class ImportBlockedError(RuntimeError):
    def __init__(self, msg: str = "Real Wiktextract import blocked by default") -> None:
        super().__init__(msg)


def _deterministic_import_key(*parts: Any) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(str(p).encode("utf-8"))
    return h.hexdigest()[:32]


@dataclass
class ProvenanceLink:
    dataset_id: str
    external_id: str | None = None
    external_id_missing: bool = False
    deterministic_key: str | None = None
    is_primary: bool = True
    confidence: float = 1.0
    notes: dict[str, Any] = field(default_factory=dict)


@dataclass
class SyntheticImportReport:
    lexemes_created: int = 0
    lexemes_updated: int = 0
    senses_created: int = 0
    translations_created: int = 0
    forms_created: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"synthetic: lexemes +{self.lexemes_created} ~{self.lexemes_updated}, "
            f"senses={self.senses_created}, translations={self.translations_created}, "
            f"forms={self.forms_created}, skipped={self.skipped}, errors={len(self.errors)}"
        )


def _assert_synthetic_mode(path: Path, dataset_id: str = "synthetic") -> None:
    if REAL_IMPORT_ALLOWED:
        logger.warning("REAL_IMPORT_ALLOWED is true; proceeding in test/override mode")
        return
    name = path.name.lower()
    if "synthetic" in name or "fixture" in name:
        return
    raise ImportBlockedError()


def validate_lemma_list_for_synthetic(lemmas: list[str], max_count: int = 20) -> list[str]:
    if len(lemmas) > max_count:
        raise ValueError(f"Batch too large: {len(lemmas)} > {max_count}")
    seen = set()
    cleaned: list[str] = []
    for w in lemmas:
        if not isinstance(w, str):
            raise ValueError("lemma must be str")
        nw = w.strip()
        if not nw:
            continue
        key = nw.casefold()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(nw)
    if len(cleaned) == 0:
        raise ValueError("Empty lemma list")
    return cleaned
