# Search pipeline

One HTTP entry point — `GET /api/search?q=…&limit=…` — runs a staged
pipeline. Each stage is an independent class with a single
`run(context)` method (`apps/api/app/services/search/`), so new signal
sources can be added without touching existing ones.

## Stages (in execution order)

| # | stage | file | what it does |
|---|---|---|---|
| 1 | normalize | `normalize.py` | Unicode NFC, whitespace collapse, lowercase (umlauts are preserved, `ß` kept) so `häusern` finds the stored form `Häusern` |
| 2 | exact surface | `surface.py` | direct `lookups.normalized_surface` hit → `matchType=form` (with full grammatical analysis from the stored features) |
| 3 | exact lemma | `lemma.py` | lookup on `lexemes.normalized_lemma` → `matchType=lemma` |
| 4 | morphology | `morphology_stage.py` | asks the configured `MorphologyEngine` to analyze the query, then resolves each analysis (`lemma`, `part_of_speech`) against stored lexemes → `matchType=morphology` |
| 5 | definition | `definition.py` | whole-word match against the **leading gloss** (the text before the first ` — ` separator) of sense definitions; **runs only when stages 1–4 produced zero candidates** → `matchType=definition` |
| 6 | fuzzy | `fuzzy.py` | typo fallback, **runs only when stages 1–5 produced zero candidates**: PostgreSQL `pg_trgm similarity()`; SQLite/`difflib` fallback → `matchType=fuzzy` |

Definition search deliberately matches only the English gloss that precedes
the em-dash, as a whole word (case-insensitive). The German explanation
after the em-dash is not searchable, and definitions never mix into an
exact lemma/form/normalized/morphology match — so `funktionieren` no longer
resolves to `gehen`, while a genuine gloss query (`house` → `Haus`) still
works when nothing more precise matched.

All stages write `SearchCandidate`s into a shared `SearchContext`
(`context.py`). Candidates are deduplicated per lexeme, keeping the
strongest match type.

## Ranking

`ranking.py` computes one deterministic score per candidate:

```
score = priority(matchType) * 1000      # lemma 6 > form 5 > normalized 4
      + morphological certainty * 100   # engine confidence, clamped 0..1
      + similarity * 50                 # fuzzy/definition similarity
      + frequency bonus                 # 100 / (1 + log10(rank)), 0 if unknown
```

Ties break on `(normalized_lemma, lexeme_id)` — never randomly, never on
timestamps. `GET /api/search` returns `queryType` as the match type of
the top result (`lemma`, `form`, `normalized`, `morphology`,
`definition`, `fuzzy`), or `null` when nothing matched.

## Response shape

`SearchResponse` (`apps/api/app/schemas/search.py`, mirrored in
`packages/shared-types/index.d.ts`):

- `query`, `queryType`, `morphologyEngine`
- `results[]`: `lexemeId`, `lemma`, `matchedSurface`, `matchedFormId`,
  `partOfSpeech`, `gender`, `definition`, `principalForms`,
  `frequencyRank`, `analysis` (compact grammatical features),
  `morphCertainty`, `score`, `matchType`

## Related endpoints

- `GET /api/entries/{id}` — senses, forms + features, examples with
  highlight offsets, frequency rows, relations, principal forms
- `GET /api/entries/{id}/forms`, `GET /api/entries/{id}/examples`
- `GET /api/forms/{id}` — one word form with its analysis
- `GET /api/parse?text=…` — tokenization + morphology per token
- `GET /api/health` — db/cache/engine status

## Performance notes

- Exact stages are single indexed lookups (`lookups` table).
- Response caching is optional (`CACHE_TTL_SECONDS`, Redis when
  configured, no-op otherwise); tests run with TTL 0.
- The fuzzy stage is deliberately last-resort: it never masks stronger
  matches and only fires on a total miss.
