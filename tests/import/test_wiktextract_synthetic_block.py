from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import importlib

wik = importlib.import_module("scripts.import.wiktextract_synthetic")


def test_block_real_by_default(tmp_path: Path) -> None:
    real = tmp_path / "en_wiktionary_raw.jsonl.gz"
    real.write_text("dummy", encoding="utf-8")
    try:
        wik._assert_synthetic_mode(real)
    except wik.ImportBlockedError:
        return
    raise AssertionError("should block real file by default")


def test_allow_synthetic(tmp_path: Path) -> None:
    synth = tmp_path / "wiktextract_synthetic.json"
    synth.write_text("{}", encoding="utf-8")
    wik._assert_synthetic_mode(synth)
