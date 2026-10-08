"""ORM row -> domain model converters."""

from __future__ import annotations

from app.domain import models
from app.domain.enums import RelationType
from app.orm import models as orm
from german_morphology import GrammaticalFeatures


def to_lexeme(row: orm.Lexeme) -> models.Lexeme:
    return models.Lexeme(
        id=row.id,
        lemma=row.lemma,
        normalized_lemma=row.normalized_lemma,
        language=row.language,
        part_of_speech=row.part_of_speech,
        gender=row.gender,
        register=row.register,
        domain=row.domain,
    )


def to_sense(row: orm.Sense) -> models.Sense:
    return models.Sense(
        id=row.id,
        sense_index=row.sense_index,
        definition=row.definition,
        register=row.register,
        domain=row.domain,
    )


def to_word_form(row: orm.WordForm) -> models.WordForm:
    features: GrammaticalFeatures | None = None
    if row.features is not None:
        extra = row.features.extra or {}
        features = GrammaticalFeatures.from_dict({**extra, **_features_dict(row.features)})
    return models.WordForm(
        id=row.id,
        lexeme_id=row.lexeme_id,
        surface=row.surface,
        normalized_surface=row.normalized_surface,
        form_type=row.form_type,
        is_searchable=row.is_searchable,
        features=features,
    )


def _features_dict(row: orm.MorphologicalFeatures) -> dict[str, str]:
    data: dict[str, str] = {}
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
        value = getattr(row, name)
        if value is not None:
            data[name] = value
    return data


def to_frequency(row: orm.Frequency) -> models.FrequencyInfo:
    return models.FrequencyInfo(
        corpus=row.corpus,
        rank=row.rank,
        count=row.count,
        word_form_id=row.word_form_id,
    )


def to_example(row: orm.ExampleWord) -> models.ExampleSentence:
    sentence = row.sentence
    return models.ExampleSentence(
        id=sentence.id,
        text=sentence.text,
        translation=sentence.translation,
        source=sentence.source,
        word_form_id=row.word_form_id,
        start_offset=row.start_offset,
        end_offset=row.end_offset,
    )


def to_relation(row: orm.LexicalRelation, target_lemma: str) -> models.LexicalRelationLink:
    return models.LexicalRelationLink(
        relation_type=RelationType(row.relation_type),
        target_lexeme_id=row.target_lexeme_id,
        target_lemma=target_lemma,
    )
