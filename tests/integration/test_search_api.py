"""Integration tests for GET /api/search (the milestone-critical endpoint)."""

from __future__ import annotations

import pytest


def _search(client, query: str, **params):  # type: ignore[no-untyped-def]
    response = client.get("/api/search", params={"q": query, **params})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize(
    ("query", "expected_lemma"),
    [
        ("gehen", "gehen"),
        ("ging", "gehen"),
        ("gegangen", "gehen"),
        ("Häusern", "Haus"),
    ],
)
def test_critical_resolutions(client, query: str, expected_lemma: str) -> None:  # type: ignore[no-untyped-def]
    data = _search(client, query)
    assert data["results"], f"no results for {query!r}"
    assert data["results"][0]["lemma"] == expected_lemma
    assert data["results"][0]["lexemeId"]


def test_gehen_is_a_lemma_match(client) -> None:  # type: ignore[no-untyped-def]
    data = _search(client, "gehen")
    assert data["queryType"] == "lemma"
    top = data["results"][0]
    assert top["matchType"] == "lemma"
    assert top["matchedSurface"] == "gehen"
    assert top["partOfSpeech"] == "verb"
    assert top["frequencyRank"] == 123
    assert top["principalForms"] == ["gehen", "ging", "gegangen"]


def test_ging_is_a_form_match_with_analysis(client) -> None:  # type: ignore[no-untyped-def]
    data = _search(client, "ging")
    assert data["queryType"] == "form"
    top = data["results"][0]
    assert top["matchType"] == "form"
    assert top["matchedSurface"] == "ging"
    assert top["lemma"] == "gehen"
    assert top["matchedFormId"]
    analysis = top["analysis"]
    assert analysis is not None
    assert analysis["tense"] == "Past"
    assert analysis["mood"] == "Ind"
    assert analysis["person"] == "3"


def test_gegangen_resolves_to_gehen(client) -> None:  # type: ignore[no-untyped-def]
    data = _search(client, "gegangen")
    top = data["results"][0]
    assert top["lemma"] == "gehen"
    assert top["matchType"] == "form"
    assert top["analysis"]["verb_form"] == "Part"


def test_haeusern_resolves_to_haus(client) -> None:  # type: ignore[no-untyped-def]
    data = _search(client, "Häusern")
    top = data["results"][0]
    assert top["lemma"] == "Haus"
    assert top["matchedSurface"] == "Häusern"
    assert top["partOfSpeech"] == "noun"
    assert top["gender"] == "neut"
    assert top["analysis"]["case"] == "Dat"
    assert top["analysis"]["number"] == "Plur"
    assert top["frequencyRank"] == 456


def test_lowercase_query_is_a_normalized_match(client) -> None:  # type: ignore[no-untyped-def]
    data = _search(client, "häusern")
    assert data["queryType"] == "normalized"
    assert data["results"][0]["lemma"] == "Haus"


@pytest.mark.parametrize(
    ("query", "expected_lemma"),
    [
        ("house", "Haus"),
        ("child", "Kind"),
        ("slow", "langsam"),
        ("fast", "schnell"),
        ("hike", "wandern"),
    ],
)
def test_definition_search_matches_english_gloss(  # type: ignore[no-untyped-def]
    client, query: str, expected_lemma: str
) -> None:
    # No exact/normalized/morphology match exists, so the definition stage
    # must still find the genuinely relevant lexeme.
    data = _search(client, query)
    assert data["queryType"] == "definition"
    assert data["results"]
    top = data["results"][0]
    assert top["lemma"] == expected_lemma
    assert top["matchType"] == "definition"
    assert top["definition"]


def test_german_word_only_in_explanation_is_not_a_definition_match(client) -> None:  # type: ignore[no-untyped-def]
    # "funktionieren" appears only after the em-dash in gehen's sense 2
    # ("to work; to function — funktionieren …"); matching the explanation
    # must not drag in gehen.
    data = _search(client, "funktionieren")
    assert all(item["lemma"] != "gehen" for item in data["results"])


def test_fuzzy_fallback_only_when_nothing_else_matched(client) -> None:  # type: ignore[no-untyped-def]
    data = _search(client, "gehne")  # typo: no exact/def match
    assert data["queryType"] == "fuzzy"
    assert data["results"][0]["lemma"] == "gehen"
    assert data["results"][0]["matchType"] == "fuzzy"


def test_no_results_returns_explicit_null_type(client) -> None:  # type: ignore[no-untyped-def]
    data = _search(client, "qxzzv")
    assert data["results"] == []
    assert data["queryType"] is None


def test_morphology_engine_is_reported(client) -> None:  # type: ignore[no-untyped-def]
    data = _search(client, "gehen")
    assert data["morphologyEngine"] == "fixture"


def test_limit_is_respected(client) -> None:  # type: ignore[no-untyped-def]
    data = _search(client, "gehen", limit=1)
    assert len(data["results"]) == 1


def test_missing_query_is_rejected(client) -> None:  # type: ignore[no-untyped-def]
    assert client.get("/api/search").status_code == 422
    assert client.get("/api/search", params={"q": ""}).status_code == 422


def test_exact_lemma_is_not_polluted_by_definition_matches(client) -> None:  # type: ignore[no-untyped-def]
    # "gehen" also appears in wandern's explanation. When an exact lemma
    # result exists, the definition stage must not add definition-only
    # neighbours.
    data = _search(client, "gehen")
    assert [item["lemma"] for item in data["results"]] == ["gehen"]
    assert [item["matchType"] for item in data["results"]] == ["lemma"]
