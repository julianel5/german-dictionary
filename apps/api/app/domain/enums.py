"""Controlled vocabularies used across the domain."""

from __future__ import annotations

from enum import StrEnum


class PartOfSpeech(StrEnum):
    NOUN = "noun"
    PROPER_NOUN = "proper_noun"
    VERB = "verb"
    AUXILIARY = "auxiliary"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PRONOUN = "pronoun"
    DETERMINER = "determiner"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    NUMERAL = "numeral"
    PARTICLE = "particle"
    INTERJECTION = "interjection"
    OTHER = "other"


class Gender(StrEnum):
    MASCULINE = "masc"
    FEMININE = "fem"
    NEUTER = "neut"


class FormType(StrEnum):
    LEMMA = "lemma"
    INFLECTED = "inflected"
    COMPARATIVE = "comparative"
    SUPERLATIVE = "superlative"
    DECLINED = "declined"
    PARTICIPLE = "participle"
    OTHER = "other"


class RelationType(StrEnum):
    SYNONYM = "synonym"
    ANTONYM = "antonym"
    DERIVED_FROM = "derived_from"
    DERIVES_TO = "derives_to"
    COMPONENT_OF = "component_of"
    CONTAINS_COMPONENT = "contains_component"


class MatchType(StrEnum):
    """How a search result matched the query. Explicit and honest:

    ``lemma``      - exact lemma match (normalized comparison)
    ``form``       - exact surface-form match (case-sensitive)
    ``normalized`` - surface match after case normalization
    ``morphology`` - morphology engine analysis resolved to a lexeme
    ``definition`` - definition full-text/substring match
    ``fuzzy``      - approximate string match
    """

    LEMMA = "lemma"
    FORM = "form"
    NORMALIZED = "normalized"
    MORPHOLOGY = "morphology"
    DEFINITION = "definition"
    FUZZY = "fuzzy"


#: Higher is better; used as the primary ranking signal.
MATCH_TYPE_PRIORITY: dict[MatchType, int] = {
    MatchType.LEMMA: 6,
    MatchType.FORM: 5,
    MatchType.NORMALIZED: 4,
    MatchType.MORPHOLOGY: 3,
    MatchType.DEFINITION: 2,
    MatchType.FUZZY: 1,
}
