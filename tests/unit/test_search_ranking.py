"""Search ranking unit tests."""

from __future__ import annotations

from app.domain.enums import MatchType
from app.domain.models import FrequencyInfo, SearchCandidate
from app.orm import models as orm
from app.services.search.context import SearchContext
from app.services.search.ranking import SearchRanker, match_score


def _lexeme(lexeme_id: str, lemma: str) -> orm.Lexeme:
    return orm.Lexeme(
        id=lexeme_id,
        lemma=lemma,
        normalized_lemma=lemma.lower(),
        language="de",
        part_of_speech="verb",
    )


def _candidate(lexeme_id: str, match_type: MatchType, **kwargs) -> SearchCandidate:
    return SearchCandidate(lexeme_id=lexeme_id, match_type=match_type, **kwargs)


def test_match_type_priority_dominates_frequency() -> None:
    lemma_score = match_score(_candidate("a", MatchType.LEMMA), None)
    form_score_with_freq = match_score(
        _candidate("b", MatchType.FORM),
        FrequencyInfo(corpus="c", rank=1, count=10),
    )
    assert lemma_score > form_score_with_freq


def test_frequency_breaks_ties() -> None:
    frequent = match_score(
        _candidate("a", MatchType.FORM), FrequencyInfo(corpus="c", rank=10, count=5)
    )
    rare = match_score(
        _candidate("b", MatchType.FORM), FrequencyInfo(corpus="c", rank=10_000, count=5)
    )
    unknown = match_score(_candidate("c", MatchType.FORM), None)
    assert frequent > rare > unknown


def test_morph_certainty_contributes_within_same_type() -> None:
    certain = match_score(_candidate("a", MatchType.MORPHOLOGY, morph_certainty=1.0), None)
    uncertain = match_score(_candidate("b", MatchType.MORPHOLOGY, morph_certainty=0.5), None)
    assert certain > uncertain


def test_fuzzy_similarity_contributes() -> None:
    close = match_score(_candidate("a", MatchType.FUZZY, similarity=0.9), None)
    far = match_score(_candidate("b", MatchType.FUZZY, similarity=0.4), None)
    assert close > far


def _ranked(context: SearchContext, lexemes: dict[str, orm.Lexeme], frequency):  # type: ignore[no-untyped-def]
    return SearchRanker().rank(context, lexemes, frequency)


def test_ranking_is_deterministic_regardless_of_insertion_order() -> None:
    lexemes = {
        "id-b": _lexeme("id-b", "bei"),
        "id-a": _lexeme("id-a", "an"),
        "id-c": _lexeme("id-c", "zu"),
    }
    frequency = {
        "id-b": FrequencyInfo(corpus="c", rank=100, count=9),
        "id-a": FrequencyInfo(corpus="c", rank=100, count=9),
        "id-c": FrequencyInfo(corpus="c", rank=100, count=9),
    }

    orders = [
        ["id-b", "id-a", "id-c"],
        ["id-c", "id-b", "id-a"],
        ["id-a", "id-c", "id-b"],
    ]
    results = []
    for order in orders:
        context = SearchContext(query="x")
        for lexeme_id in order:
            context.add_candidate(_candidate(lexeme_id, MatchType.FORM))
        results.append([item.lexeme.id for item in _ranked(context, lexemes, frequency)])

    assert results[0] == results[1] == results[2]
    # equal scores -> tie-break on normalized lemma alphabetically
    assert results[0] == ["id-a", "id-b", "id-c"]


def test_limit_is_applied() -> None:
    lexemes = {f"id-{i}": _lexeme(f"id-{i}", f"w{i:02d}") for i in range(5)}
    context = SearchContext(query="x", limit=2)
    for lexeme_id in lexemes:
        context.add_candidate(_candidate(lexeme_id, MatchType.FORM))
    ranked = _ranked(context, lexemes, {})
    assert len(ranked) == 2


def test_higher_priority_match_wins_in_context_merge() -> None:
    context = SearchContext(query="ging")
    context.add_candidate(_candidate("lex", MatchType.MORPHOLOGY, matched_surface="ging"))
    context.add_candidate(_candidate("lex", MatchType.FORM, matched_surface="ging"))
    assert context.candidates["lex"].match_type is MatchType.FORM
    # lower priority arriving later must not overwrite
    context.add_candidate(_candidate("lex", MatchType.DEFINITION))
    assert context.candidates["lex"].match_type is MatchType.FORM
