from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import importlib

wik = importlib.import_module("scripts.import.wiktextract_synthetic")


def test_deterministic_key_stable() -> None:
    k1 = wik._deterministic_import_key("ds", "lemma", "noun", "et", "ctx")
    k2 = wik._deterministic_import_key("ds", "lemma", "noun", "et", "ctx")
    assert k1 == k2
    k3 = wik._deterministic_import_key("ds", "lemma", "noun", "et2", "ctx")
    assert k1 != k3


def test_report_summary() -> None:
    r = wik.SyntheticImportReport(lexemes_created=1, translations_created=2)
    s = r.summary()
    assert "synthetic" in s
