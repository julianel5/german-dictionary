"""Domain model -> DTO converters."""

from __future__ import annotations

from app.domain import models as domain
from app.schemas.common import GrammaticalFeaturesDTO, LexemeDTO
from app.schemas.entries import (
    ExampleHighlightDTO,
    ExampleSentenceDTO,
    FrequencyDTO,
    RelationDTO,
    SenseDTO,
    WordFormDTO,
)
from german_morphology import GrammaticalFeatures as DomainFeatures


def features_dto(features: DomainFeatures | None) -> GrammaticalFeaturesDTO | None:
    if features is None:
        return None
    data = features.as_dict()
    extra = {
        key: str(value)
        for key, value in data.items()
        if key
        not in {
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
        }
    }
    return GrammaticalFeaturesDTO(
        case=features.case,
        number=features.number,
        gender=features.gender,
        person=features.person,
        tense=features.tense,
        mood=features.mood,
        degree=features.degree,
        voice=features.voice,
        verb_form=features.verb_form,
        adjective_form=features.adjective_form,
        extra=extra,
    )


def lexeme_dto(lexeme: domain.Lexeme) -> LexemeDTO:
    return LexemeDTO(
        id=lexeme.id,
        lemma=lexeme.lemma,
        language=lexeme.language,
        part_of_speech=lexeme.part_of_speech,
        gender=lexeme.gender,
        register=lexeme.register,
        domain=lexeme.domain,
    )


def sense_dto(sense: domain.Sense) -> SenseDTO:
    return SenseDTO(
        id=sense.id,
        sense_index=sense.sense_index,
        definition=sense.definition,
        register=sense.register,
        domain=sense.domain,
    )


def word_form_dto(form: domain.WordForm) -> WordFormDTO:
    return WordFormDTO(
        id=form.id,
        surface=form.surface,
        normalized_surface=form.normalized_surface,
        form_type=form.form_type,
        is_searchable=form.is_searchable,
        features=features_dto(form.features),
    )


def example_dto(example: domain.ExampleSentence) -> ExampleSentenceDTO:
    highlights: list[ExampleHighlightDTO] = []
    if example.word_form_id is not None and example.start_offset is not None:
        highlights.append(
            ExampleHighlightDTO(
                word_form_id=example.word_form_id,
                surface=example.text[example.start_offset : example.end_offset],
                start_offset=example.start_offset,
                end_offset=example.end_offset,
            )
        )
    return ExampleSentenceDTO(
        id=example.id,
        text=example.text,
        translation=example.translation,
        source=example.source,
        highlights=highlights,
    )


def frequency_dto(frequency: domain.FrequencyInfo) -> FrequencyDTO:
    return FrequencyDTO(
        corpus=frequency.corpus,
        rank=frequency.rank,
        count=frequency.count,
        word_form_id=frequency.word_form_id,
    )


def relation_dto(relation: domain.LexicalRelationLink) -> RelationDTO:
    return RelationDTO(
        relation_type=relation.relation_type.value,
        lexeme_id=relation.target_lexeme_id,
        lemma=relation.target_lemma,
    )
