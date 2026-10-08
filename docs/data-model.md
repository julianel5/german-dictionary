# Data model

Relational schema implemented in SQLAlchemy 2.x (`apps/api/app/orm`),
migrated with Alembic (`apps/api/alembic/versions/`). IDs are opaque
UUID strings; the seeder derives them deterministically (`uuid5`) so
re-seeding produces identical ids.

## Entity-relationship overview

```
lexemes 1─n senses
lexemes 1─n word_forms ──1 morphological_features
lexemes 1─n frequencies
lexemes 1─n lexical_relations (source)   ──n lexemes (target)
lookups (denormalized index: normalized_surface → lexeme/word_form)
example_sentences 1─n example_words (word_form + character offsets)
```

## Tables

### `lexemes`
Dictionary headword entry.

| column | type | notes |
|---|---|---|
| `id` | uuid str (PK) | deterministic in seed data |
| `lemma` | str(255) | display form, e.g. `Häuser` |
| `normalized_lemma` | str(255), indexed | case/apostrophe-folded for lookup |
| `language` | str(8) | default `de` |
| `part_of_speech` | str(32) | `noun`, `verb`, `adjective`, … |
| `gender` | str(16)? | `masc`/`fem`/`neut`/`plural` (nouns) |
| `register` / `domain` | str(64)? | e.g. `colloquial` |
| `created_at` / `updated_at` | datetime | server default `now` |

### `senses`
One dictionary entry may have several numbered senses.

`lexeme_id` FK, `sense_index` (1-based ordering), `definition` (text),
`register`, `domain`.

### `word_forms`
Every inflected/derived surface form we can search directly.

`lexeme_id` FK, `surface`, `normalized_surface` (indexed),
`form_type` (`lemma`, `past`, `participle`, `declined`, `comparative`,
`superlative`, …), `is_searchable` (skip accidental collisions).

### `morphological_features`
One row per `word_form` with the grammatical description: `case`,
`number`, `gender`, `person`, `tense`, `mood`, `degree`, `voice`,
`verb_form`, `adjective_form` (all nullable strings using compact codes
such as `Nom`, `Plur`, `Past`, `Ind`, `Fin`, `Part`, `Sup`), plus an
`extra` JSON column for rare attributes. Compact codes are translated to
full German labels only at the presentation layer
(`apps/web/app/utils/format.ts`).

### `lookups`
Denormalized search index built by the loader/`rebuild_lookups`
maintenance script:

`normalized_surface` → (`lexeme_id`, optional `word_form_id`).

Unique on `normalized_surface + word_form_id` semantics; backs the
exact-surface and exact-lemma stages without joins.

### `frequencies`
`lexeme_id` and optional `word_form_id`, `corpus`, `rank` (1 = most
frequent), `count`. Frequency feeds the ranking bonus and the
`Häufigkeit` badge in the UI.

### `lexical_relations`
Directed edges between lexemes: `source_lexeme_id`,
`target_lexeme_id`, `relation_type` (`synonym`, `antonym`, `hyponym`,
`hyperonym`). Unresolved targets are rejected at import time.

### `example_sentences` / `example_words`
Sentence-level: `text`, optional `translation`, `source`. Link rows pin
`word_form_id` (nullable) with `start_offset`/`end_offset` character
offsets so the UI can highlight the inflected form exactly; offset
integrity is validated (slice equals `surface`).

## Normalization contract

`scripts/normalized.py` defines the JSON contract between importers and
the database loader (`NormalizedDictionary`, `NormalizedFrequency`).
Cross-validation rejects orphan relation targets, out-of-range offsets,
duplicate sense indices and missing lemma forms before anything touches
the database.
