"""Principal ("dictionary head") forms for result cards and entry pages.

Picks the forms a learner expects to see next to the lemma:

* verbs:        lemma · past tense · participle   (gehen · ging · gegangen)
* nouns:        singular · plural                 (Haus · Häuser)
* adjectives:   positive · comparative · superlative (schnell · schneller · schnellsten)
"""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.models import Lexeme, WordForm

_MAX_FORMS = 3
_VERBS = {"verb", "auxiliary"}


def principal_forms(
    lexeme: Lexeme,
    forms: Sequence[WordForm],
    *,
    max_forms: int = _MAX_FORMS,
) -> list[str]:
    searchable = sorted(
        (form for form in forms if form.is_searchable),
        key=lambda form: (form.surface, form.id),
    )
    ordered: list[str] = []

    def add(surface: str | None) -> None:
        if surface and surface not in ordered:
            ordered.append(surface)

    lemma_form = next((form for form in searchable if form.surface == lexeme.lemma), None)
    add(lemma_form.surface if lemma_form else None)

    def features(form: WordForm) -> dict[str, str]:
        if form.features is None:
            return {}
        return {key: value for key, value in form.features.as_dict().items() if value}

    if lexeme.part_of_speech in _VERBS:
        past = next(
            (
                form
                for form in searchable
                if features(form).get("tense") == "Past"
                and features(form).get("mood") == "Ind"
                and features(form).get("number") == "Sing"
            ),
            None,
        )
        add(past.surface if past else None)
        participle = next(
            (form for form in searchable if features(form).get("verb_form") == "Part"),
            None,
        )
        add(participle.surface if participle else None)
    elif lexeme.part_of_speech == "noun":
        plural = next(
            (
                form
                for form in searchable
                if features(form).get("number") == "Plur"
                and features(form).get("case") in (None, "Nom")
            ),
            None,
        ) or next((form for form in searchable if features(form).get("number") == "Plur"), None)
        add(plural.surface if plural else None)
    elif lexeme.part_of_speech == "adjective":
        for degree in ("Cmp", "Sup"):
            form = next(
                (
                    candidate
                    for candidate in searchable
                    if features(candidate).get("degree") == degree
                ),
                None,
            )
            add(form.surface if form else None)

    if len(ordered) < 2:
        for form in searchable:
            if len(ordered) >= max_forms:
                break
            add(form.surface)
    return ordered[:max_forms]
