"""Import dictionary data: raw -> processed -> (optionally) the database.

Usage::

    python -m scripts.import.import_dictionary
    python -m scripts.import.import_dictionary --source data/raw/my_source.json
    python -m scripts.import.import_dictionary --load

The raw source file is opened read-only and never modified. The processed
representation is written to ``data/processed/`` and can be inspected or
versioned independently before being loaded.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from scripts.paths import REPO_ROOT, ensure_paths

ensure_paths()

logger = logging.getLogger("scripts.import.import_dictionary")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import dictionary data")
    parser.add_argument(
        "--source",
        type=Path,
        default=REPO_ROOT / "data" / "raw" / "dictionary.json",
        help="raw source file (read-only)",
    )
    parser.add_argument(
        "--processed",
        type=Path,
        default=REPO_ROOT / "data" / "processed" / "dictionary.json",
        help="processed output file",
    )
    parser.add_argument(
        "--load",
        action="store_true",
        help="load the processed data into the database",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # NB: `scripts.import` cannot be referenced with dotted syntax
    # (import is a keyword); inside the package use a relative import.
    from scripts.normalized import RecordValidationError

    from .pipeline import process_dictionary

    try:
        data = process_dictionary(args.source, args.processed)
    except (FileNotFoundError, ValueError, RecordValidationError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"normalized {len(data.lexemes)} lexemes -> {args.processed}")

    if args.load:
        from app.db import get_session_factory, reset_engine
        from scripts.dbload import DatabaseLoader
        from scripts.schema import ensure_schema

        reset_engine()
        ensure_schema()
        with get_session_factory()() as session:
            report = DatabaseLoader(session).load_dictionary(data)
            session.commit()
        print(report.summary())
        if report.errors:
            return 1
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(main())
