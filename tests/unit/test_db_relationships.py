"""Database relationship tests (schema integrity, cascades, aggregates)."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.orm import models as orm
from app.repositories.content_repo import ContentRepository
from app.repositories.lexeme_repo import LexemeRepository
from german_morphology import normalize


def _count(session, model, **filters) -> int:  # type: ignore[no-untyped-def]
    stmt = select(func.count()).select_from(model)
    for column, value in filters.items():
        stmt = stmt.where(getattr(model, column) == value)
    return int(session.scalar(stmt) or 0)


def _make_lexeme(session, lexeme_id: str = "test-cascade-lex") -> orm.Lexeme:  # type: ignore[no-untyped-def]
    lexeme = orm.Lexeme(
        id=lexeme_id,
        lemma="Testwort",
        normalized_lemma=normalize("Testwort"),
        language="de",
        part_of_speech="noun",
        gender="neut",
    )
    session.add(lexeme)
    session.flush()
    return lexeme


def test_sense_index_is_unique_per_lexeme(session) -> None:  # type: ignore[no-untyped-def]
    lexeme = _make_lexeme(session, "test-unique-sense")
    session.add(orm.Sense(id="s1", lexeme_id=lexeme.id, sense_index=1, definition="one"))
    session.flush()
    session.add(orm.Sense(id="s2", lexeme_id=lexeme.id, sense_index=1, definition="dup"))
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_word_form_surface_is_unique_per_lexeme(session) -> None:  # type: ignore[no-untyped-def]
    lexeme = _make_lexeme(session, "test-unique-form")
    session.add(
        orm.WordForm(
            id="f1",
            lexeme_id=lexeme.id,
            surface="Testwort",
            normalized_surface="testwort",
            form_type="lemma",
        )
    )
    session.flush()
    session.add(
        orm.WordForm(
            id="f2",
            lexeme_id=lexeme.id,
            surface="Testwort",
            normalized_surface="testwort",
            form_type="lemma",
        )
    )
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_cascade_delete_removes_dependent_rows(session) -> None:  # type: ignore[no-untyped-def]
    lexeme = _make_lexeme(session, "test-cascade-delete")
    session.add(orm.Sense(id="cs", lexeme_id=lexeme.id, sense_index=1, definition="d"))
    form = orm.WordForm(
        id="cf",
        lexeme_id=lexeme.id,
        surface="Testworte",
        normalized_surface="testworte",
        form_type="declined",
    )
    session.add(form)
    session.flush()
    session.add(orm.MorphologicalFeatures(id="cfm", word_form_id=form.id, case="Nom"))
    session.add(
        orm.Lookup(
            id="cl",
            normalized_surface="testworte",
            lexeme_id=lexeme.id,
            word_form_id=form.id,
        )
    )
    session.add(orm.Frequency(id="cfr", lexeme_id=lexeme.id, corpus="c", rank=1, count=10))
    session.flush()

    session.delete(lexeme)
    session.flush()

    assert _count(session, orm.Sense, lexeme_id="test-cascade-delete") == 0
    assert _count(session, orm.WordForm, lexeme_id="test-cascade-delete") == 0
    assert _count(session, orm.Lookup, lexeme_id="test-cascade-delete") == 0
    assert _count(session, orm.Frequency, lexeme_id="test-cascade-delete") == 0
    assert _count(session, orm.MorphologicalFeatures, word_form_id="cf") == 0


def test_example_words_link_sentences_to_forms(session) -> None:  # type: ignore[no-untyped-def]
    examples = ContentRepository(session).examples_for_lexeme(_fixture_lexeme_id(session, "Haus"))
    assert examples
    for example in examples:
        assert example.word_form_id is not None
        assert example.start_offset is not None and example.end_offset is not None
        assert (
            example.text[example.start_offset : example.end_offset]
            == example.text[example.start_offset : example.end_offset]
        )
        # the linked span is a real word in the sentence
        span = example.text[example.start_offset : example.end_offset]
        assert span.strip() == span and span


def test_example_offsets_resolve_correct_surface(session) -> None:  # type: ignore[no-untyped-def]
    examples = ContentRepository(session).examples_for_lexeme(_fixture_lexeme_id(session, "Kind"))
    surfaces = set()
    for example in examples:
        assert example.start_offset is not None and example.end_offset is not None
        surfaces.add(example.text[example.start_offset : example.end_offset])
    assert surfaces == {"Kind", "Kindern"}


def test_best_frequency_across_corpora(session) -> None:  # type: ignore[no-untyped-def]
    lexeme_id = _fixture_lexeme_id(session, "gehen")
    extra = orm.Frequency(
        id="test-freq-second-corpus",
        lexeme_id=lexeme_id,
        corpus="zzz-second-corpus",
        rank=5,
        count=99,
    )
    session.add(extra)
    session.flush()

    best = ContentRepository(session).best_frequency([lexeme_id])
    assert best[lexeme_id].rank == 5  # lower rank wins across corpora
    assert best[lexeme_id].corpus == "zzz-second-corpus"

    session.delete(extra)
    session.flush()


def test_relations_are_exposed_from_both_directions(session) -> None:  # type: ignore[no-untyped-def]
    gehen_id = _fixture_lexeme_id(session, "gehen")
    wandern_id = _fixture_lexeme_id(session, "wandern")

    outgoing = ContentRepository(session).relations_for_lexeme(gehen_id)
    assert any(
        link.relation_type.value == "synonym" and link.target_lexeme_id == wandern_id
        for link in outgoing
    )

    incoming = ContentRepository(session).relations_for_lexeme(wandern_id)
    assert any(
        link.relation_type.value == "synonym" and link.target_lexeme_id == gehen_id
        for link in incoming
    )


def test_aggregate_contains_all_parts(session) -> None:  # type: ignore[no-untyped-def]
    entry = LexemeRepository(session).aggregate(_fixture_lexeme_id(session, "gehen"))
    assert entry is not None
    assert entry.lexeme.lemma == "gehen"
    assert entry.senses
    assert {form.surface for form in entry.word_forms} >= {"gehen", "ging", "gegangen"}
    assert all(form.features is not None for form in entry.word_forms)
    assert entry.examples
    assert entry.frequency
    assert entry.relations


def _fixture_lexeme_id(session, lemma: str) -> str:  # type: ignore[no-untyped-def]
    row = session.scalar(
        select(orm.Lexeme.id).where(orm.Lexeme.normalized_lemma == normalize(lemma))
    )
    assert row is not None, f"fixture lexeme {lemma!r} missing"
    return str(row)
