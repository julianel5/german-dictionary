"""Generate the curated common-English-lemma list from a Wiktionary frequency page.

Procedure: ``generate-common-lemmas/1.0``.

Reads the raw wikitext of an en.wiktionary frequency-list page (approved frame
for the common-words coverage study, see ``docs/data-import/common-words-study.md``
§1.3, option A) and emits a UTF-8 TSV of single-token lemmas with the *rank*
surface, keeping the highest-ranked occurrence when a token appears more than
once.

Filters (documented in the study methodology §2):

- F0: skip rows struck through in the source (``<s>``).
- F1: skip tokens containing whitespace (multi-word surfaces).
- F2: keep only alphabetic tokens; a single intra-word apostrophe is allowed
  (contractions such as ``don't`` / ``I'm`` are lexemes with their own
  en.wiktionary entries and fall in the ``function`` category at measurement);
  leading/trailing apostrophes, hyphens, digits and any other characters are
  rejected.
- F5: cap the list to the first ``--limit`` surviving tokens.

Inflected-form classification (F3) and POS assignability (F4) are *measured*
against the en.wiktionary extract by ``common_coverage.py`` — never guessed
here — and are reported as ``inflected_only`` / ``missing`` in the report.

Every ``#`` line in the output is self-describing provenance (frame URL,
revision, licence, retrieval timestamp, source sha256, filter counts) and is
recorded verbatim by the measurement script.

Everything the generator reads lives outside the repository; the output goes to
gitignored ``data/processed/`` and the raw frame text is never committed.

Usage::

    python -m scripts.import.generate_common_lemmas \\
        --source <frame>.wikitext --meta <frame>.meta.json \\
        --out data/processed/common-lemmas.tsv [--limit 1000]
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import sys
from pathlib import Path

SEED = "20261008"
PROCEDURE_VERSION = "generate-common-lemmas/1.0"
LICENCE = "CC BY-SA 4.0 (contents of en.wiktionary)"
FRAME_URL = (
    "https://en.wiktionary.org/wiki/Wiktionary:Frequency_lists/TV/2006/1-1000"
)

_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|\|\s*(.*?)\s*\|\|")
_LINK_RE = re.compile(r"\[\[([^][|#]+)(?:#[^][|]*)?(?:\|([^][]+))?\]\]")
_SURFACE_RE = re.compile(r"^[a-zA-Z]+(?:'[a-zA-Z]+)*$")


def _parse_row(line: str) -> tuple[int, str, str | None] | None:
    if "<s>" in line:
        return None
    row = _ROW_RE.match(line)
    if row is None:
        return None
    rank = int(row.group(1))
    cell = row.group(2)
    link = _LINK_RE.search(cell)
    if link is None:
        return None
    surface = link.group(2) if link.group(2) else link.group(1)
    surface = surface.strip()
    count_match = re.search(r"\|\|\s*([\d,]+)", line)
    count = count_match.group(1) if count_match else None
    return rank, surface, count


def _filter(surface: str) -> tuple[str | None, str]:
    if re.search(r"\s", surface):
        return None, "F1"
    if _SURFACE_RE.fullmatch(surface) is None:
        return None, "F2"
    return surface, ""


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_meta(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {"revid": "unknown", "timestamp": "unknown", "user": "unknown"}
    pages = json.loads(path.read_text(encoding="utf-8"))["query"]["pages"]
    for page in pages.values():
        rev = page.get("revisions", [{}])[0]
        return {
            "revid": rev.get("revid", "unknown"),
            "timestamp": rev.get("timestamp", "unknown"),
            "user": rev.get("user", "unknown"),
        }
    return {"revid": "unknown", "timestamp": "unknown", "user": "unknown"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path,
                        help="raw wikitext of the frame page")
    parser.add_argument("--meta", type=Path, default=None,
                        help="MediaWiki revisions meta JSON (for revid)")
    parser.add_argument("--out", type=Path,
                        default=Path("data/processed/common-lemmas.tsv"),
                        help="output TSV path (gitignored)")
    parser.add_argument("--limit", type=int, default=1000,
                        help="max surviving tokens (F5), default 1000")
    return parser


def generate(source: Path, meta: Path | None,
             limit: int) -> tuple[list[tuple[int, str, str | None]], dict]:
    counts = {"rows": 0, "F0": 0, "F1": 0, "F2": 0, "duplicates": 0,
              "beyond_limit": 0}
    kept: list[tuple[int, str, str | None]] = []
    seen: set[str] = set()
    with source.open(encoding="utf-8") as f:
        for line in f:
            counts["rows"] += 1
            parsed = _parse_row(line)
            if parsed is None:
                if "<s>" in line:
                    counts["F0"] += 1
                continue
            rank, surface, count = parsed
            surface, tag = _filter(surface)
            if surface is None:
                counts[tag] += 1
                continue
            key = surface.casefold()
            if key in seen:
                counts["duplicates"] += 1
                continue
            seen.add(key)
            if len(kept) >= limit:
                counts["beyond_limit"] += 1
                continue
            kept.append((rank, surface, count))
    return kept, counts


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    kept, counts = generate(args.source, args.meta, args.limit)
    if len(kept) == 0:
        print("generate-common-lemmas: no tokens survived the filters",
              file=sys.stderr)
        return 1
    meta = _read_meta(args.meta)
    source_sha = _sha256(args.source)
    fetched = _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds")
    total = counts["rows"]
    dropped = sum(counts[k] for k in ("F0", "F1", "F2"))
    lines = [
        f"# {PROCEDURE_VERSION}",
        "# frame: Wiktionary:Frequency lists/TV/2006/1-1000 (en.wiktionary)",
        f"# url: {FRAME_URL}",
        f"# source_revid: {meta['revid']}",
        f"# source_rev_timestamp: {meta['timestamp']}",
        f"# source_rev_edited_by: {meta['user']}",
        f"# licence: {LICENCE}",
        f"# retrieved: {fetched}",
        f"# source_sha256: {source_sha}",
        f"# rows: {total}  struck_F0: {counts['F0']}  space_F1: {counts['F1']}  "
        f"surface_F2: {counts['F2']}  beyond_limit_F5: {counts['beyond_limit']}  "
        f"duplicates_dropped: {counts['duplicates']}  lemmas: {len(kept)}",
        "# category: derived from the en.wiktionary extract at measurement time",
        "# columns: word | category (empty; derived) | rank:N (frame rank)",
    ]
    for rank, surface, _count in kept:
        lines.append(f"{surface}\t\trank:{rank}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"lemmas: {len(kept)} kept from {total} rows "
        f"(struck={counts['F0']}, space={counts['F1']}, "
        f"surface={counts['F2']}, dupes={counts['duplicates']}, "
        f"beyond_limit={counts['beyond_limit']}) dropped={dropped}",
        file=sys.stderr,
    )
    print(f"lemmas written: {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())