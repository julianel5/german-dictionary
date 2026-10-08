"""Rebuild the lookup index from word forms.

Usage::

    python -m scripts.maintenance.rebuild_lookups

Useful after bulk data edits or schema experiments: the lookup index is
fully derived data (normalized surface -> lexeme + word form) and can
always be regenerated. Uses the same deterministic ids as the loader.
"""

from __future__ import annotations

import argparse

from scripts.paths import ensure_paths

ensure_paths()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rebuild the lookup index")
    parser.add_argument("--database-url", default=None, help="override DATABASE_URL")
    return parser


def rebuild() -> int:
    from sqlalchemy import delete, select

    from app.db import get_session_factory
    from app.orm import models as orm
    from scripts.dbload import id_for

    created = 0
    with get_session_factory()() as session:
        session.execute(delete(orm.Lookup))
        forms = session.scalars(select(orm.WordForm).where(orm.WordForm.is_searchable.is_(True)))
        for form in forms:
            session.add(
                orm.Lookup(
                    id=id_for("lookup", form.normalized_surface, form.id),
                    normalized_surface=form.normalized_surface,
                    lexeme_id=form.lexeme_id,
                    word_form_id=form.id,
                )
            )
            created += 1
        session.commit()
    print(f"lookup index rebuilt: {created} entries")
    return created


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.database_url:
        import os

        os.environ["DATABASE_URL"] = args.database_url
        from app.db import reset_engine

        reset_engine()
    return 0 if rebuild() >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
