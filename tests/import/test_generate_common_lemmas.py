"""Tests for ``scripts.import.generate_common_lemmas`` (proc 1.0)."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

common = importlib.import_module("scripts.import.common_coverage")
generator = importlib.import_module("scripts.import.generate_common_lemmas")

WIKITEXT = (
    "|'''rank'''||'''word'''||'''count'''\n"
    "|-\n"
    "| 1  || [[you#English|you]]  || 1222421 (see also ya)\n"
    "|-\n"
    "| 2  || [[I#English|I]]  or [[I#English|I]] . || 1052546\n"
    "|-\n"
    "| 3  || [[can't#English|can't]] || 62602\n"
    "|-\n"
    "| 4  || [[Mr#English|Mr]] . || 20053\n"
    "|-\n"
    "| 5  || [[house#English|house]]  or [[House#English|House]]  || 14458\n"
    "|-\n"
    "| 6  || [[everything#English|everything]]  || 23714\n"
    "|-\n"
    "| 7  || [[everything#English|everything]] 's || 2316\n"
    "|-\n"
    "| 8  || [['em#English|'em]]  || 5590\n"
    "|-\n"
    "| 9  || [[y'know#English|y'know]]  || 3395\n"
    "|-\n"
    "| 10 || <s>[[nbsp#English|nbsp]] </s> || <s>2824</s>\n"
    "|-\n"
    "| 11 || [[go-go#English|go-go]] || 100\n"
)


def _meta(path: Path, revid: int = 123) -> None:
    path.write_text(
        json.dumps(
            {
                "query": {
                    "pages": {
                        "1": {
                            "revisions": [
                                {
                                    "revid": revid,
                                    "timestamp": "2024-01-02T03:04:05Z",
                                    "user": "someone",
                                }
                            ]
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )


def test_parse_row() -> None:
    assert generator._parse_row("| 1  || [[you#English|you]]  || 1222421\n") == (
        1,
        "you",
        "1222421",
    )
    assert generator._parse_row(
        "| 2  || [[I#English|I]]  or [[I#English|I]] . || 1052546\n"
    ) == (2, "I", "1052546")
    assert generator._parse_row(
        "| 8  || [['em#English|'em]]  || 5590\n"
    ) == (8, "'em", "5590")
    assert generator._parse_row(
        "| 10 || <s>[[nbsp#English|nbsp]] </s> || <s>2824</s>\n"
    ) is None


def test_filter_surfaces() -> None:
    assert generator._filter("house") == ("house", "")
    assert generator._filter("can't") == ("can't", "")
    assert generator._filter("'em") == (None, "F2")
    assert generator._filter("y'know") == ("y'know", "")
    assert generator._filter("go-go") == (None, "F2")
    assert generator._filter("everything's two") == (None, "F1")


def test_generate_filters_dedupes_and_preserves_rank(tmp_path: Path) -> None:
    source = tmp_path / "frame.wikitext"
    source.write_text(WIKITEXT, encoding="utf-8")
    kept, counts = generator.generate(source, None, limit=1000)
    assert [s for _, s, _ in kept] == [
        "you", "I", "can't", "Mr", "house", "everything", "y'know",
    ]
    assert [r for r, _, _ in kept] == [1, 2, 3, 4, 5, 6, 9]
    assert counts["F0"] == 1
    assert counts["F1"] == 0
    assert counts["F2"] == 2
    assert counts["duplicates"] == 1
    assert counts["beyond_limit"] == 0


def test_generate_caps_at_limit(tmp_path: Path) -> None:
    source = tmp_path / "frame.wikitext"
    source.write_text(WIKITEXT, encoding="utf-8")
    kept, counts = generator.generate(source, None, limit=4)
    assert [s for _, s, _ in kept] == ["you", "I", "can't", "Mr"]
    assert counts["beyond_limit"] == 3


def test_main_end_to_end(tmp_path: Path) -> None:
    source = tmp_path / "frame.wikitext"
    meta = tmp_path / "frame.meta.json"
    out = tmp_path / "lemmas.tsv"
    source.write_text(WIKITEXT, encoding="utf-8")
    _meta(meta)
    assert generator.main(
        ["--source", str(source), "--meta", str(meta),
         "--out", str(out), "--limit", "1000"]
    ) == 0
    text = out.read_text(encoding="utf-8")
    header = [line for line in text.splitlines() if line.startswith("#")]
    body = [line for line in text.splitlines() if not line.startswith("#")]
    assert any("# source_revid: 123" in line for line in header)
    assert any("# licence:" in line for line in header)
    assert any(line.startswith("# rows:") and "lemmas: 7" in line
               for line in header)
    assert "you\t\trank:1" in body
    assert "can't\t\trank:3" in body
    entries, _ = common.read_lemma_list(out)
    assert [e["word"] for e in entries] == [
        "you", "I", "can't", "Mr", "house", "everything", "y'know",
    ]
    assert entries[5]["rank"] == "6"
    assert all(e["category"] is None for e in entries)