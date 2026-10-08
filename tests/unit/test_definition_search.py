"""Unit tests for the definition relevance policy (leading gloss, whole word)."""

from __future__ import annotations

from app.repositories.search_repos import leading_gloss, matches_gloss


def test_leading_gloss_extracts_english_part() -> None:
    assert leading_gloss("to go; to walk — sich zu Fuß bewegen") == "to go; to walk"


def test_leading_gloss_without_separator_is_whole_definition() -> None:
    assert leading_gloss("house") == "house"


def test_matches_gloss_ignores_explanation() -> None:
    definition = "to work; to function — funktionieren (von Geräten und Maschinen)"
    assert matches_gloss(definition, "function")
    # The German word appears only after the em-dash and must not match.
    assert not matches_gloss(definition, "funktionieren")


def test_matches_gloss_requires_whole_word() -> None:
    definition = "to work; to function — funktionieren"
    assert matches_gloss(definition, "work")
    assert not matches_gloss(definition, "funct")  # substring, not a word


def test_matches_gloss_is_case_insensitive() -> None:
    assert matches_gloss("house — Gebäude", "House")
    assert matches_gloss("house — Gebäude", "HOUSE")


def test_matches_gloss_rejects_empty_and_single_char() -> None:
    assert not matches_gloss("house — Gebäude", "")
    assert not matches_gloss("house — Gebäude", "h")


def test_matches_gloss_handles_regex_metacharacters() -> None:
    assert not matches_gloss("house — Gebäude", "h(ou")
    assert matches_gloss("a+b — Zeichen", "a+b")
