"""Integration tests for entries, forms and examples endpoints."""

from __future__ import annotations


def _lexeme_id(client, query: str) -> str:  # type: ignore[no-untyped-def]
    response = client.get("/api/search", params={"q": query})
    assert response.status_code == 200
    return response.json()["results"][0]["lexemeId"]


def test_entry_detail(client) -> None:  # type: ignore[no-untyped-def]
    lexeme_id = _lexeme_id(client, "gehen")
    response = client.get(f"/api/entries/{lexeme_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["lexeme"]["lemma"] == "gehen"
    assert data["lexeme"]["partOfSpeech"] == "verb"
    assert len(data["senses"]) >= 2
    assert data["senses"][0]["senseIndex"] == 1
    assert "to go" in data["senses"][0]["definition"]

    surfaces = {form["surface"] for form in data["forms"]}
    assert {"gehen", "gehst", "geht", "ging", "gingen", "gegangen"} <= surfaces

    ging = next(form for form in data["forms"] if form["surface"] == "ging")
    assert ging["features"]["tense"] == "Past"
    assert ging["features"]["person"] == "3"

    assert data["examples"]
    for example in data["examples"]:
        for highlight in example["highlights"]:
            start, end = highlight["startOffset"], highlight["endOffset"]
            assert example["text"][start:end] == highlight["surface"]

    assert any(item["rank"] == 123 for item in data["frequency"])
    assert any(
        item["relationType"] == "synonym" and item["lemma"] == "wandern"
        for item in data["relations"]
    )
    assert data["principalForms"] == ["gehen", "ging", "gegangen"]


def test_entry_forms_subresource(client) -> None:  # type: ignore[no-untyped-def]
    lexeme_id = _lexeme_id(client, "Haus")
    response = client.get(f"/api/entries/{lexeme_id}/forms")
    assert response.status_code == 200
    data = response.json()
    assert data["lemma"] == "Haus"
    surfaces = {form["surface"] for form in data["forms"]}
    assert {"Haus", "Häuser", "Häusern"} <= surfaces
    hausern = next(form for form in data["forms"] if form["surface"] == "Häusern")
    assert hausern["features"]["case"] == "Dat"
    assert hausern["features"]["number"] == "Plur"


def test_entry_examples_subresource(client) -> None:  # type: ignore[no-untyped-def]
    lexeme_id = _lexeme_id(client, "Kind")
    response = client.get(f"/api/entries/{lexeme_id}/examples")
    assert response.status_code == 200
    data = response.json()
    assert data["lemma"] == "Kind"
    assert len(data["examples"]) == 2
    highlighted = {example["highlights"][0]["surface"] for example in data["examples"]}
    assert highlighted == {"Kind", "Kindern"}


def test_single_form_endpoint(client) -> None:  # type: ignore[no-untyped-def]
    lexeme_id = _lexeme_id(client, "gehen")
    forms = client.get(f"/api/entries/{lexeme_id}/forms").json()["forms"]
    gegangen = next(form for form in forms if form["surface"] == "gegangen")
    response = client.get(f"/api/forms/{gegangen['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["surface"] == "gegangen"
    assert data["formType"] == "participle"
    assert data["features"]["verb_form"] == "Part"
    assert data["normalizedSurface"] == "gegangen"


def test_unknown_ids_return_404(client) -> None:  # type: ignore[no-untyped-def]
    assert client.get("/api/entries/does-not-exist").status_code == 404
    assert client.get("/api/entries/does-not-exist/forms").status_code == 404
    assert client.get("/api/entries/does-not-exist/examples").status_code == 404
    assert client.get("/api/forms/does-not-exist").status_code == 404
