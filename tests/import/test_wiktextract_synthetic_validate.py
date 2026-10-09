from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import importlib

wik = importlib.import_module("scripts.import.wiktextract_synthetic")


def test_validate_small_batch() -> None:
    res = wik.validate_lemma_list_for_synthetic(["cat", "dog", "cat"])
    assert res == ["cat", "dog"]


def test_validate_max_20() -> None:
    many = [f"w{i}" for i in range(21)]
    try:
        wik.validate_lemma_list_for_synthetic(many)
    except ValueError:
        return
    raise AssertionError("should fail on >20")
