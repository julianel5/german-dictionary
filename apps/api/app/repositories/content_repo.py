"""Data-access for examples, frequency and lexical relations."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.domain import models as domain
from app.domain.enums import RelationType
from app.orm import models as orm
from app.repositories import mappers

#: Relation types whose inverse is not identical.
_INVERSE: dict[str, str] = {
    RelationType.DERIVED_FROM.value: RelationType.DERIVES_TO.value,
    RelationType.DERIVES_TO.value: RelationType.DERIVED_FROM.value,
    RelationType.COMPONENT_OF.value: RelationType.CONTAINS_COMPONENT.value,
    RelationType.CONTAINS_COMPONENT.value: RelationType.COMPONENT_OF.value,
}


def invert_relation(relation_type: str) -> str:
    return _INVERSE.get(relation_type, relation_type)


class ContentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    # -- examples --------------------------------------------------------
    def examples_for_lexeme(self, lexeme_id: str) -> list[domain.ExampleSentence]:
        stmt = (
            select(orm.ExampleWord)
            .join(
                orm.ExampleSentence, orm.ExampleWord.example_sentence_id == orm.ExampleSentence.id
            )
            .join(orm.WordForm, orm.ExampleWord.word_form_id == orm.WordForm.id)
            .where(orm.WordForm.lexeme_id == lexeme_id)
            .options(joinedload(orm.ExampleWord.sentence))
            .order_by(
                orm.ExampleSentence.text,
                orm.ExampleWord.start_offset,
                orm.ExampleWord.id,
            )
        )
        seen: set[str] = set()
        examples: list[domain.ExampleSentence] = []
        for row in self._session.scalars(stmt):
            if row.example_sentence_id in seen:
                continue
            seen.add(row.example_sentence_id)
            examples.append(mappers.to_example(row))
        return examples

    # -- frequency -------------------------------------------------------
    def best_frequency(self, lexeme_ids: Sequence[str]) -> dict[str, domain.FrequencyInfo]:
        """Lowest rank per lexeme across all corpora (ties: corpus, id)."""
        ids = list(dict.fromkeys(lexeme_ids))
        if not ids:
            return {}
        stmt = (
            select(orm.Frequency)
            .where(orm.Frequency.lexeme_id.in_(ids))
            .order_by(
                orm.Frequency.lexeme_id,
                orm.Frequency.rank,
                orm.Frequency.corpus,
                orm.Frequency.id,
            )
        )
        best: dict[str, domain.FrequencyInfo] = {}
        for row in self._session.scalars(stmt):
            best.setdefault(row.lexeme_id, mappers.to_frequency(row))
        return best

    def frequency_for_lexeme(self, lexeme_id: str) -> list[domain.FrequencyInfo]:
        stmt = (
            select(orm.Frequency)
            .where(orm.Frequency.lexeme_id == lexeme_id)
            .order_by(orm.Frequency.rank, orm.Frequency.corpus, orm.Frequency.id)
        )
        return [mappers.to_frequency(row) for row in self._session.scalars(stmt)]

    # -- relations -------------------------------------------------------
    def relations_for_lexeme(self, lexeme_id: str) -> list[domain.LexicalRelationLink]:
        outgoing_stmt = (
            select(orm.LexicalRelation)
            .where(orm.LexicalRelation.source_lexeme_id == lexeme_id)
            .options(joinedload(orm.LexicalRelation.target_lexeme))
            .order_by(orm.LexicalRelation.target_lexeme_id, orm.LexicalRelation.id)
        )
        incoming_stmt = (
            select(orm.LexicalRelation)
            .where(orm.LexicalRelation.target_lexeme_id == lexeme_id)
            .options(joinedload(orm.LexicalRelation.source_lexeme))
            .order_by(orm.LexicalRelation.source_lexeme_id, orm.LexicalRelation.id)
        )
        links: list[domain.LexicalRelationLink] = []
        for row in self._session.scalars(outgoing_stmt):
            links.append(
                domain.LexicalRelationLink(
                    relation_type=RelationType(row.relation_type),
                    target_lexeme_id=row.target_lexeme_id,
                    target_lemma=row.target_lexeme.lemma,
                )
            )
        for row in self._session.scalars(incoming_stmt):
            links.append(
                domain.LexicalRelationLink(
                    relation_type=RelationType(invert_relation(row.relation_type)),
                    target_lexeme_id=row.source_lexeme_id,
                    target_lemma=row.source_lexeme.lemma,
                )
            )
        links.sort(
            key=lambda link: (link.relation_type.value, link.target_lemma, link.target_lexeme_id)
        )
        return links
