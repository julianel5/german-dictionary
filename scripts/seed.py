"""Deterministic database seeder.

Usage::

    python -m scripts.seed            # idempotent (upserts fixture data)
    python -m scripts.seed --reset    # wipe dictionary data first

The fixture dataset (data/fixtures/) exercises the whole stack: lemmas,
inflected forms, structured features, lookup index, relations, examples
and frequency ranks.
"""

from __future__ import annotations

import argparse
import logging
import sys

from scripts.paths import ensure_paths

ensure_paths()

logger = logging.getLogger("scripts.seed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed the database with fixture data")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="delete all dictionary data before seeding",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="override DATABASE_URL for this run",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.database_url:
        import os

        os.environ["DATABASE_URL"] = args.database_url

    from app.db import get_session_factory, reset_engine
    from scripts.dbload import DatabaseLoader, delete_all
    from scripts.fixtures import load_fixture_dictionary, load_fixture_frequency
    from scripts.schema import ensure_schema

    reset_engine()
    method = ensure_schema()
    logger.info("schema ready (%s)", method)

    dictionary = load_fixture_dictionary()
    frequency = load_fixture_frequency()

    factory = get_session_factory()
    with factory() as session:
        if args.reset:
            delete_all(session)
            logger.info("existing dictionary data cleared")
        loader = DatabaseLoader(session)
        dictionary_report = loader.load_dictionary(dictionary)
        frequency_report = loader.load_frequency(frequency)
        session.commit()

    print(f"schema: {method}")
    print("dictionary:")
    print(dictionary_report.summary())
    print("frequency:")
    print(frequency_report.summary())

    problems = dictionary_report.errors + frequency_report.errors
    if problems:
        print(f"finished with {len(problems)} error(s)", file=sys.stderr)
        return 1
    print("seed complete")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    raise SystemExit(main())
