"""Integration tests for GET /api/parse and GET /api/health."""

from __future__ import annotations


def test_parse_tokenizes_and_analyzes(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/api/parse", params={"text": "Ich ging nach Haus."})
    assert response.status_code == 200
    data = response.json()
    assert data["engine"] == "fixture"

    tokens = {token["surface"]: token for token in data["tokens"]}
    assert set(tokens) == {"Ich", "ging", "nach", "Haus"}

    ging = tokens["ging"]
    assert ging["start"] == 4 and ging["end"] == 8
    assert ging["analyses"]
    analysis = ging["analyses"][0]
    assert analysis["lemma"] == "gehen"
    assert analysis["features"]["tense"] == "Past"
    assert analysis["engine"] == "fixture"

    haus = tokens["Haus"]
    assert haus["analyses"][0]["lemma"] == "Haus"


def test_parse_offsets_slice_original_text(client) -> None:  # type: ignore[no-untyped-def]
    text = "Das Kind spielt im Garten."
    data = client.get("/api/parse", params={"text": text}).json()
    for token in data["tokens"]:
        assert text[token["start"] : token["end"]] == token["surface"]


def test_parse_requires_text(client) -> None:  # type: ignore[no-untyped-def]
    assert client.get("/api/parse").status_code == 422


def test_health(client) -> None:  # type: ignore[no-untyped-def]
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"
    assert data["cache"] is False  # no Redis configured in tests
    assert data["morphologyEngine"] == "fixture"
