"""Load normalized records into the database.

Idempotent: all primary keys are deterministic (uuid5 over stable record
keys), so re-running a loader updates rows in place instead of duplicating
them. Load order matters: dictionary first, frequency second (form-level
frequency rows reference word forms).
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.orm import models as orm
from german_morphology import normalize
from scripts.normalized import (
    NormalizedDictionary,
    NormalizedExample,
    NormalizedFeatures,
    NormalizedFrequency,
    NormalizedLexeme,
)

_NAMESPACE = uuid.UUID("4fd7a1a6-0d4a-4d0f-9d9c-6c5e6a1b2f31")

#: Word-boundary match used to locate linked forms inside example sentences.
_BOUNDARY = r"(?<!\w){}(?!\w)"


def id_for(*parts: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, "|".join(parts)))


@dataclass
class LoadReport:
    lexemes_created: int = 0
    lexemes_updated: int = 0
    senses: int = 0
    word_forms: int = 0
    lookups: int = 0
    relations: int = 0
    examples: int = 0
    example_words: int = 0
    frequencies: int = 0
    errors: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"lexemes: +{self.lexemes_created} ~{self.lexemes_updated}",
            f"senses: {self.senses}  word_forms: {self.word_forms}  lookups: {self.lookups}",
            f"relations: {self.relations}  examples: {self.examples} "
            f"(links: {self.example_words})  frequencies: {self.frequencies}",
        ]
        if self.errors:
            lines.append(f"errors: {len(self.errors)}")
            lines.extend(f"  - {message}" for message in self.errors)
        return "\n".join(lines)


class DatabaseLoader:
    def __init__(self, session: Session) -> None:
        self._session = session

    # -- dictionary ------------------------------------------------------
    def load_dictionary(self, data: NormalizedDictionary) -> LoadReport:
        report = LoadReport()
        lexeme_ids = {
            (lex.language, lex.lemma, lex.part_of_speech): id_for(
                "lexeme", lex.language, lex.lemma, lex.part_of_speech
            )
            for lex in data.lexemes
        }
        for lexeme in data.lexemes:
            self._load_lexeme(lexeme, lexeme_ids, report)
        self._session.flush()
        for lexeme in data.lexemes:
            self._load_relations(lexeme, lexeme_ids, report)
        for lexeme in data.lexemes:
            for example in lexeme.examples:
                self._load_example(example, lexeme, lexeme_ids, report)
        self._session.flush()
        return report

    def _load_lexeme(
        self,
        lexeme: NormalizedLexeme,
        lexeme_ids: dict[tuple[str, str, str], str],
        report: LoadReport,
    ) -> None:
        lexeme_id = lexeme_ids[(lexeme.language, lexeme.lemma, lexeme.part_of_speech)]
        row = self._session.get(orm.Lexeme, lexeme_id)
        if row is None:
            row = orm.Lexeme(id=lexeme_id)
            self._session.add(row)
            report.lexemes_created += 1
        else:
            report.lexemes_updated += 1
        row.lemma = lexeme.lemma
        row.normalized_lemma = normalize(lexeme.lemma)
        row.language = lexeme.language
        row.part_of_speech = lexeme.part_of_speech
        row.gender = lexeme.gender
        row.register = lexeme.register
        row.domain = lexeme.domain

        # Senses and forms are replaced wholesale for determinism.
        self._session.execute(delete(orm.Sense).where(orm.Sense.lexeme_id == lexeme_id))
        for sense in lexeme.senses:
            self._session.add(
                orm.Sense(
                    id=id_for("sense", lexeme_id, str(sense.sense_index)),
                    lexeme_id=lexeme_id,
                    sense_index=sense.sense_index,
                    definition=sense.definition,
                    register=sense.register,
                    domain=sense.domain,
                )
            )
            report.senses += 1

        self._session.execute(delete(orm.WordForm).where(orm.WordForm.lexeme_id == lexeme_id))
        for form in lexeme.forms:
            word_form_id = id_for("word_form", lexeme_id, form.surface)
            normalized_surface = normalize(form.surface)
            self._session.add(
                orm.WordForm(
                    id=word_form_id,
                    lexeme_id=lexeme_id,
                    surface=form.surface,
                    normalized_surface=normalized_surface,
                    form_type=form.form_type,
                    is_searchable=form.is_searchable,
                )
            )
            report.word_forms += 1
            if form.features is not None:
                self._session.add(
                    self._features_row(word_form_id, form.features, lexeme, form.surface)
                )
            if form.is_searchable:
                self._session.add(
                    orm.Lookup(
                        id=id_for("lookup", normalized_surface, word_form_id),
                        normalized_surface=normalized_surface,
                        lexeme_id=lexeme_id,
                        word_form_id=word_form_id,
                    )
                )
                report.lookups += 1
        self._session.flush()

    @staticmethod
    def _features_row(
        word_form_id: str,
        features: NormalizedFeatures,
        lexeme: NormalizedLexeme,
        surface: str,
    ) -> orm.MorphologicalFeatures:
        extra = dict(features.extra) or None
        row = orm.MorphologicalFeatures(
            id=id_for("features", word_form_id),
            word_form_id=word_form_id,
            extra=extra,
        )
        for name in (
            "case",
            "number",
            "gender",
            "person",
            "tense",
            "mood",
            "degree",
            "voice",
            "verb_form",
            "adjective_form",
        ):
            setattr(row, name, getattr(features, name))
        return row

    def _load_relations(
        self,
        lexeme: NormalizedLexeme,
        lexeme_ids: dict[tuple[str, str, str], str],
        report: LoadReport,
    ) -> None:
        source_id = lexeme_ids[(lexeme.language, lexeme.lemma, lexeme.part_of_speech)]
        self._session.execute(
            delete(orm.LexicalRelation).where(orm.LexicalRelation.source_lexeme_id == source_id)
        )
        for relation in lexeme.relations:
            target_id = self._resolve_lexeme_id(relation.target_lemma, lexeme_ids, lexeme)
            if target_id is None:
                report.errors.append(
                    f"{lexeme.lemma}: unresolved relation target {relation.target_lemma!r}"
                )
                continue
            self._session.add(
                orm.LexicalRelation(
                    id=id_for("relation", source_id, target_id, relation.relation_type),
                    source_lexeme_id=source_id,
                    target_lexeme_id=target_id,
                    relation_type=relation.relation_type,
                )
            )
            report.relations += 1

    @staticmethod
    def _resolve_lexeme_id(
        lemma: str,
        lexeme_ids: dict[tuple[str, str, str], str],
        requester: NormalizedLexeme,
    ) -> str | None:
        for (language, lexeme_lemma, _pos), lexeme_id in lexeme_ids.items():
            if language == requester.language and lexeme_lemma == lemma:
                return lexeme_id
        return None

    def _load_example(
        self,
        example: NormalizedExample,
        lexeme: NormalizedLexeme,
        lexeme_ids: dict[tuple[str, str, str], str],
        report: LoadReport,
    ) -> None:
        sentence_id = id_for("example", example.text)
        row = self._session.get(orm.ExampleSentence, sentence_id)
        if row is None:
            row = orm.ExampleSentence(id=sentence_id)
            self._session.add(row)
        row.text = example.text
        row.translation = example.translation
        row.source = example.source
        report.examples += 1

        self._session.execute(
            delete(orm.ExampleWord).where(orm.ExampleWord.example_sentence_id == sentence_id)
        )
        for link in example.linked_forms:
            target_id = self._resolve_lexeme_id(link.lemma, lexeme_ids, lexeme)
            if target_id is None:
                report.errors.append(f"{lexeme.lemma}: example links unknown lemma {link.lemma!r}")
                continue
            word_form_id = id_for("word_form", target_id, link.surface)
            if self._session.get(orm.WordForm, word_form_id) is None:
                report.errors.append(f"{lexeme.lemma}: example links unknown form {link.surface!r}")
                continue
            span = _find_span(example.text, link.surface)
            if span is None:
                report.errors.append(
                    f"{lexeme.lemma}: surface {link.surface!r} not found in "
                    f"example {example.text!r}"
                )
                continue
            start, end = span
            self._session.add(
                orm.ExampleWord(
                    id=id_for("example_word", sentence_id, word_form_id, str(start)),
                    example_sentence_id=sentence_id,
                    word_form_id=word_form_id,
                    start_offset=start,
                    end_offset=end,
                )
            )
            report.example_words += 1

    # -- frequency -------------------------------------------------------
    def load_frequency(self, data: NormalizedFrequency) -> LoadReport:
        report = LoadReport()
        for entry in data.entries:
            lexeme_id = self._find_lexeme_id(entry.lemma)
            if lexeme_id is None:
                report.errors.append(f"frequency: unknown lemma {entry.lemma!r}")
                continue
            word_form_id: str | None = None
            if entry.surface is not None:
                word_form_id = id_for("word_form", lexeme_id, entry.surface)
                if self._session.get(orm.WordForm, word_form_id) is None:
                    report.errors.append(
                        f"frequency: unknown form {entry.surface!r} of {entry.lemma!r}"
                    )
                    continue
            frequency_id = id_for("frequency", data.corpus, lexeme_id, word_form_id or "")
            row = self._session.get(orm.Frequency, frequency_id)
            if row is None:
                row = orm.Frequency(id=frequency_id)
                self._session.add(row)
            row.lexeme_id = lexeme_id
            row.word_form_id = word_form_id
            row.corpus = data.corpus
            row.rank = entry.rank
            row.count = entry.count
            report.frequencies += 1
        self._session.flush()
        return report

    def _find_lexeme_id(self, lemma: str) -> str | None:
        stmt = select(orm.Lexeme.id).where(orm.Lexeme.normalized_lemma == normalize(lemma))
        return self._session.scalar(stmt)


def delete_all(session: Session) -> None:
    """Remove all dictionary data (fixture-friendly full reset)."""
    for table in (
        orm.ExampleWord,
        orm.ExampleSentence,
        orm.Frequency,
        orm.LexicalRelation,
        orm.Lookup,
        orm.MorphologicalFeatures,
        orm.WordForm,
        orm.Sense,
        orm.Lexeme,
    ):
        session.execute(delete(table))
    session.commit()


def _find_span(text: str, surface: str) -> tuple[int, int] | None:
    pattern = re.compile(_BOUNDARY.format(re.escape(surface)))
    match = pattern.search(text)
    if match is not None:
        return match.start(), match.end()
    # Fall back to a plain substring match (e.g. surface adjacent to
    # punctuation that breaks the word-boundary assumption).
    index = text.find(surface)
    if index == -1:
        return None
    return index, index + len(surface)
