"""Lookup index tests."""

from __future__ import annotations

from sqlalchemy import func, select

from app.orm import models as orm
from app.repositories.lookup_repo import LookupRepository
from german_morphology import normalize


def test_every_searchable_form_is_indexed(session) -> None:  # type: ignore[no-untyped-def]
    searchable = session.scalar(
        select(func.count()).select_from(orm.WordForm).where(orm.WordForm.is_searchable.is_(True))
    )
    indexed = session.scalar(select(func.count()).select_from(orm.Lookup))
    assert indexed == searchable
    assert (searchable or 0) > 0


def test_lookup_resolves_case_insensitive_query(session) -> None:  # type: ignore[no-untyped-def]
    repo = LookupRepository(session)
    rows = repo.surface_candidates(normalize("Häusern"))
    assert rows
    surfaces = {form.surface for _lookup, form in rows}
    assert "Häusern" in surfaces

    rows_lower = repo.surface_candidates(normalize("häusern"))
    assert {form.surface for _lookup, form in rows_lower} == surfaces


def test_lookup_maps_surface_to_correct_lexeme(session) -> None:  # type: ignore[no-untyped-def]
    repo = LookupRepository(session)
    rows = repo.surface_candidates(normalize("ging"))
    assert len(rows) == 1
    lookup, form = rows[0]
    lexeme = session.get(orm.Lexeme, lookup.lexeme_id)
    assert lexeme is not None
    assert lexeme.lemma == "gehen"
    assert form.surface == "ging"
    assert lookup.word_form_id == form.id


def test_non_searchable_forms_are_not_indexed(session) -> None:  # type: ignore[no-untyped-def]
    from german_morphology import normalize as norm

    lexeme = orm.Lexeme(
        id="test-nosearch-lexeme",
        lemma="Nosearch",
        normalized_lemma=norm("Nosearch"),
        language="de",
        part_of_speech="noun",
    )
    form = orm.WordForm(
        id="test-nosearch-form",
        lexeme_id=lexeme.id,
        surface="Nosearchen",
        normalized_surface=norm("Nosearchen"),
        form_type="declined",
        is_searchable=False,
    )
    session.add(lexeme)
    session.add(form)
    session.flush()

    repo = LookupRepository(session)
    assert repo.surface_candidates(norm("nosearchen")) == []

    session.delete(lexeme)
    session.flush()
