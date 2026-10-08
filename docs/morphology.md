# Morphology

The API never talks to a morphology library directly. It depends on the
`MorphologyEngine` protocol from the `german_morphology` package
(`services/morphology/`); the concrete engine is a runtime setting.

## The protocol

```python
@runtime_checkable
class MorphologyEngine(Protocol):
    @property
    def name(self) -> str: ...

    def analyze(self, surface: str) -> list[MorphologicalAnalysis]: ...
```

`MorphologicalAnalysis` carries `surface`, `lemma`,
`normalized_lemma`, `part_of_speech`, compact `GrammaticalFeatures`,
`confidence` (0..1) and the engine `name`. Multiple analyses per surface
are allowed (homographs); the search pipeline evaluates them all.

## Engines

Selection via `MORPHOLOGY_ENGINE` (`app/config.py`, default `auto`):

| value | behavior |
|---|---|
| `auto` | use spaCy `de_core_news_sm` if it loads, otherwise no engine |
| `spacy` | spaCy engine; raises if the model is missing |
| `fixture` | deterministic offline engine (tests, demos without spaCy) |

### spaCy engine (`spacy_engine.py`)

Wraps `de_core_news_sm` (`spacy.load`). spaCy's morphologizer/tagger
provides the lemma; its features (Tense, Mood, Person, Number, Case,
Gender, Degree, VerbForm…) are mapped onto our compact codes (`Past`,
`Ind`, `3`, `Plur`, `Dat`, …). Confidence is the tagger probability
when available.

Verified behavior (this milestone):

| input | result |
|---|---|
| `ging`, `gingen`, `gegangen` | `gehen` (verb, Past/Part) |
| `Häusern` | `Haus` (dative plural) |
| `gehst` | handled by the lookup index (spaCy alone would return the wrong lemma) |

Known limitations: occasional odd lemmas on unknown words (e.g.
`schnellsen`); those are contained because the morphology stage only
accepts analyses that resolve to a **stored** lexeme — garbage lemmas
simply produce no candidates.

### Fixture engine (`fixture_engine.py`)

A small deterministic table covering the seed dataset (gehen, wandern,
Haus, Kind, schnell, langsam). Used by the test suite
(`MORPHOLOGY_ENGINE=fixture` in `tests/conftest.py`) so tests never need
spaCy data, and available for fully offline demos.

## Why not DEMorphy?

DEMorphy — the initially considered pure-Python analyzer — is not
installable from PyPI: the name there hosts a dependency-confusion stub
(`demorphy-999.9.9`, ~1.5 kB, build fails); the real project is an
unmaintained GitHub repo requiring a manual dictionary download. spaCy's
small German model was verified against the required resolutions before
being adopted.

## Where morphology appears

1. **Search stage 4** (`morphology_stage.py`): analyze query → resolve
   to stored lexemes → `matchType=morphology`.
2. **`GET /api/parse`**: token-by-token analysis for the UI/future
   readers, reported as `engine` in the response.
3. **Web UI**: grammatical features are rendered as German labels
   (`apps/web/app/utils/format.ts`); `GET /api/search` also returns
   `morphologyEngine` so the UI can show which engine answered
   (fixture data is labeled honestly).
