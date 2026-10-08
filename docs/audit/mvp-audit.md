# MVP Audit — German Dictionary Core

Status: **audit complete** (read-only; no product code changed).
Scope: the "dictionary core" milestone as shipped — repo, runtime behaviour, tests, data and docs.
Deliverable: this report. No next-milestone work was started.

## Method

Static review of every first-party source file, plus dynamic verification:
running the existing test suites/linters and probing the running Docker stack
(`docker compose up`, API on `:8000`, web on `:3000`) with edge-case queries.

Verified on this machine:

- backend: `python -m pytest` → **78 passed**; `ruff check .` → clean;
  `ruff format --check .` → 83 files already formatted.
- frontend: `npm test` → **24 passed** (Vitest); lint/prettier were clean at
  milestone time and are unchanged by this audit (no files edited).
- live stack: `db`, `redis`, `api`, `web` all `Up`; health OK; queries below
  produced live results. Container/host versions: Python 3.13, Node 24,
  PostgreSQL 16-alpine, Redis 7-alpine.

Severity scale:

- **P0** blocks reliable operation — none found.
- **P1** must fix before real (large) data / production use.
- **P2** product/robustness improvement, not a crash.
- **P3** polish, docs, minor.

---

## Executive summary

The MVP is a coherent, genuinely working vertical slice: a layered FastAPI
backend, a staged search pipeline, a replaceable morphology engine, a small
but real import pipeline, a Nuxt 4 UI and honest tests. The architecture
matches the docs, the seed is deterministic and idempotent, and the search
contract is explicit and truthful (`queryType = null` when nothing matches;
match types are classified by actual evidence, not guessed).

Two issues deserve attention before the next milestone:

1. **P1-1 — the morphology engine is reconstructed on every request**, which
   reloads the spaCy model each time (`/api/parse` and `/api/search` measured
   ~1.1–2.2 s/request). This is the single biggest functional drag and it also
   undermines the response cache.
2. **P1-2 — the definition stage has no relevance gate**, so
   `funktionieren → gehen` and `gehen → wandern` (via definitions). Correct and
   tested for the 6-word fixture, but at real dictionary scale this will
   produce noisy low-precision results.

Nothing found is P0. The largest category is documentation drift (P3): several
documented enum values, features and behaviours do not match the code.

---

## 1. Verified architecture

The claimed architecture is real and, with noted exceptions, accurate.

- **Monorepo, single Python project.** Root `pyproject.toml` installs `app`,
  `german_morphology` and `scripts` (`apps/api/app`, `services/morphology/german_morphology`,
  `scripts`). Confirmed.
- **Layering.** Routers → services → repositories → ORM, with plain domain
  dataclasses (`app/domain`) between ORM and Pydantic DTOs (`app/schemas`).
  Routers contain no SQL. Confirmed across all five routers.
- **ORM / schema.** SQLAlchemy 2.x typed models; 9 tables (`lexemes`, `senses`,
  `word_forms`, `morphological_features`, `lookups`, `frequencies`,
  `lexical_relations`, `example_sentences`, `example_words`). FKs `ON DELETE CASCADE`,
  uniqueness on `senses(lexeme_id,sense_index)`, `word_forms(lexeme_id,surface)`,
  `lookups(normalized_surface,word_form_id)`, `frequencies(corpus,lexeme_id,word_form_id)`,
  `lexical_relations(source,target,type)`, `morphological_features(word_form_id)`.
  SQLite gets `PRAGMA foreign_keys=ON` on connect (`apps/api/app/db.py:23`).
- **Alembic.** One revision `4ba08e47a971` matches the models, and adds the
  PostgreSQL-only pieces: `CREATE EXTENSION IF NOT EXISTS pg_trgm` and a GIN
  index on `to_tsvector('german', definition)`
  (`apps/api/alembic/versions/4ba08e47a971_initial_schema.py:156`).
- **Dialect-aware search.** Definition search = PostgreSQL FTS
  (`to_tsvector`/`plainto_tsquery`/`ts_rank`) with a substring fallback; fuzzy =
  `pg_trgm similarity()` with a `difflib` fallback (`app/repositories/search_repos.py`).
  The FTS/trigram path is only reachable on PostgreSQL; the SQLite fallback is
  what the hermetic tests exercise.
- **Morphology abstraction.** API depends only on the `MorphologyEngine`
  protocol; the factory selects `auto|spacy|fixture|none`. The concrete engine
  is imported lazily, so the API never imports spaCy unless needed. Confirmed.
- **Cache.** Optional Redis response cache, degrades to no-op on any error
  (`app/services/cache.py`). Cache keys are versioned, case-sensitive and
  sha256-hashed (`app/services/search/service.py:20`). Empty result sets are
  not cached. Confirmed live (9 keys present after probes).
- **Frontend.** Nuxt 4 (SSR build served from `.output/server/index.mjs`),
  Tailwind 4, client-side `$fetch` against `NUXT_PUBLIC_API_BASE`. Shared types
  mirror the API DTOs. Confirmed.

### Component reality check (claim → verified)

| Claim | Verified |
|---|---|
| Staged pipeline `normalize→surface→lemma→morphology→definition→fuzzy→rank→build` | yes, one class per stage |
| Deterministic ranking, ties on `(normalized_lemma, lexeme_id)` | yes (`ranking.py`) |
| SQLite fallback for zero-setup dev | yes (`effective_database_url → data/dev.db`) |
| Docker stack seeds on boot | yes (compose command), but not the image `CMD` — see P3-3 |
| Fixture engine for hermetic tests | yes (`MORPHOLOGY_ENGINE=fixture`) |

---

## 2. Actual data sources

- **Dictionary + frequency shown in the product are 100 % hand-authored
  fixtures**, not real dictionary data:
  - `data/fixtures/dictionary.json` — 6 lexemes (gehen, wandern, Haus, Kind,
    schnell, langsam), 7 senses, 23 word forms, 2 relations, 8 examples.
  - `data/fixtures/frequency.json` — 7 rows, corpus label `fixture-de-2026`.
  - Both declare `"source": "Hand-authored project fixture"`.
- `data/raw/` contains **no source data** — only a README describing the
  licensing/manifest requirements for real sources (`data/raw/README.md`).
- `data/processed/` exists (importer output target) but there is no committed
  processed dataset of substance.
- The importer contract (`scripts/normalized.py`) is real and validated; the
  importers read any `--source` JSON in that shape. **No external corpus is
  bundled or downloaded.**
- The `fixture_engine` (morphology) is a separate static table that includes
  forms not present in the dictionary fixture (e.g. `laufen`, `läuft`). See
  P2-4.

Conclusion: the milestone is a **fully offline demonstration**, as documented.
There is no real lexical content yet, so "does the product find real German
words" is not yet testable.

---

## 3. Implemented vs. missing capabilities

### Implemented and verified

- `GET /api/search` — staged search, explicit `queryType`, principal forms,
  analysis, frequency rank, scored/deterministically ordered results, caching.
- `GET /api/entries/{id}` (+ `/forms`, `/examples`) — aggregate with senses,
  forms + features, examples with highlight offsets, frequency, relations,
  principal forms; 404 for unknown ids.
- `GET /api/forms/{id}` — single form with analysis.
- `GET /api/parse?text=…` — tokenization + per-token analyses.
- `GET /api/health` — db / cache / engine status.
- Import pipeline (`scripts.import.*`) + deterministic `scripts.seed` +
  `rebuild_lookups` maintenance.
- Morphology engines: spaCy (`de_core_news_sm`), fixture, or none.
- Nuxt UI: search box, result cards, entry page (senses, forms table, examples
  with highlighting, frequency, relations), loading/empty/error states.
- Tests: pytest unit + API integration; Vitest for frontend utilities and the
  result card.

### Missing (explicitly out of scope for this milestone, confirmed absent)

- Accounts/auth, SRS/word lists, audio, CEFR metadata, browser extension,
  hosted search, cloud deployment.
- No real lexical dataset, no automatic download, no full-text ingestion of a
  real dictionary.
- No pagination/offset on search (only `limit ≤ 50`) — see P3-5.
- No compound-word segmentation beyond stored relations (documented).
- No `Sent:`/`Nicht-` style search filters, no language switch (`language` is
  fixed to `de`).

---

## 4. Search pipeline and defects

Pipeline order is exactly as documented. Match types are assigned by real
evidence; the exact-surface stage distinguishes `form` (raw-cased equality)
from `normalized` (equality only after normalization). Live probes:

| query | `queryType` | results (lemma / matchType) |
|---|---|---|
| `gehen` | lemma | gehen/lemma, wandern/definition |
| `ging` | form | gehen/form |
| `gegangen` | form | gehen/form |
| `Haus` | lemma | Haus/lemma |
| `Häusern` | form | Haus/form |
| `häusern` | normalized | Haus/normalized |
| `HÄUSERN` | normalized | Haus/normalized |
| `hausern` | fuzzy | Haus/fuzzy, wandern/fuzzy |
| `funktionieren` | definition | gehen/definition |
| `die`, `ist`, `xyzzy` | `null` | (none) |
| `""` | — | HTTP 422 |

Ranking behaves as documented (match-type priority dominates; frequency breaks
ties; deterministic). The known cache-key case-sensitivity bug is already fixed
and covered by `tests/unit/test_search_cache.py`.

### Defects / concerns

**P1-2 — Definition stage runs unconditionally with no relevance gate.**
`DefinitionStage.run` adds a definition candidate for every sense whose
definition matches, regardless of how well the query matches or whether
higher-precision stages already produced results
(`app/services/search/definition.py:17`, wired unconditionally in
`pipeline.py:74`). With 6 lexemes this yields the (tested) `funktionieren→gehen`
and `gehen→wandern` results. At real scale every query that is a common word or
a stem present in definitions will drag in many low-relevance rows. There is no
minimum rank/similarity threshold and no "skip if exact stages already matched"
guard, unlike fuzzy (which is correctly gated by `context.is_empty`). This is
the most likely source of real-world search noise.

**P2-1 — Canonical Unicode equivalence downgrades the match type.**
`ExactSurfaceStage` decides `FORM` vs `NORMALIZED` by comparing the stored
surface to the **raw** query (`surface.py:28,30`), not the NFC-normalized query.
Probe: NFD `Häusern` (`H` + `a` + combining diaeresis) returns
`queryType=normalized` instead of `form`. The result is still correct; only the
label is downgraded. Copy/paste from some sources yields NFD.

**P2-2 — Definition/fuzzy backends diverge between dialects.**
The README/docs present SQLite as an "honest degradation", but the two paths
are not equivalent:
- fuzzy thresholds differ on the same scale? No — `_PG_TRGM_THRESHOLD = 0.3`
  vs `_DIFFLIB_CUTOFF = 0.55`, so the same query can return a different fuzzy
  set on PostgreSQL vs SQLite (e.g. `hausern→wandern` on PG).
- the substring fallback uses `Sense.definition.like(...)` (case-sensitive on
  PostgreSQL, ASCII-case-insensitive on SQLite); the FTS path stems and
  case-folds. The definition stage also passes the raw `context.query`, not the
  normalized one.
- `pg_trgm` only exists if the Alembic migration ran (it does, in Compose);
  a DB brought up via `create_all` (e.g. `scripts.seed` on a fresh clone, or a
  bare image) has **no** `pg_trgm`/FTS GIN index, and the repository falls back
  to substring search with a logged warning. The result shape is the same, the
  behaviour is not.

**Other pipeline observations**

- Definition candidates never carry `similarity`, so the `similarity*50`
  ranking term and the "definition similarity" wording in `docs/search.md` do
  not apply to them.
- `MorphologyStage` passes the raw query to the engine but resolves the stored
  form via `context.normalized`; with the spaCy engine the matched surface is
  the raw query, which can differ in case from the stored form.
- Search responses are cached only when `results` is non-empty; this means
  "no result" queries recompute every time (minor, and arguably intentional).

---

## 5. Morphology limitations

The abstraction is clean and the "never fabricate" rule is upheld
(unknown surfaces → empty list; analyses whose lemma is not a stored lexeme are
dropped).

**P1-1 — Engine instance rebuilt per request (dominant performance issue).**
`get_morphology_engine()` has **no caching** (`app/deps.py:22`); it calls
`create_morphology_engine(...)` on every request. The factory constructs a new
`SpacyMorphologyEngine`, whose `_nlp` is `None`, so the first `analyze()` call
executes `spacy.load("de_core_news_sm")` (`spacy_engine.py:58`). In `auto`
mode the factory even calls `candidate.analyze("gehen")` at construction time
to verify the model loads (`factory.py:47`), so **every** search, parse and
health request reloads the model. Measured live:

```
/api/parse  : 1092, 1363, 1194, 1349 ms   (one short sentence, repeated)
/api/search :  996 ms cold, 2211 ms "warm" (still builds engine before cache lookup)
/api/entries:  21, 21, 24 ms              (no engine → fast)
```

Contrasting entry latency (~21 ms) shows the engine construction is the cost,
not the DB. Because the engine dependency is resolved **before**
`SearchService.search` consults Redis, the cache does not save the model load
on search either. The fix is a process-wide singleton (the same pattern already
used for `ResponseCache` in `deps.py:27`), but per the audit scope this was
**not** implemented.

Additional morphology notes:

- spaCy `de_core_news_sm` limitations are documented and contained
  (`gehst` handled by lookup; odd lemmas dropped if not stored).
- **P3-2d — `docs/morphology.md` states "Confidence is the tagger probability
  when available", but `spacy_engine` hard-codes `confidence=1.0`** and the
  comment says the sm model exposes no calibrated probability. Doc contradicts
  code (the code is the honest choice, and `SearchResultCard`'s
  "unsichere Analyse" branch is therefore currently unreachable with spaCy).
- `GrammaticalFeatures.extra` round-trips through a JSON column; fine.
- `adjective_form` is derived from the STTS tag (`ADJA`/`ADJD`), not UD
  `Degree`; only attributive/adverbial is distinguished.
- **P2-4 — the fixture engine and the fixture dictionary are out of sync**:
  `fixture_engine.py` knows `laufen/läuft/lief/gelaufen` and `schnellsten`,
  but `dictionary.json` has no `laufen` lexeme. A query such as `läuft`
  therefore analyses to lemma `laufen` and then resolves to nothing (dropped) —
  consistent with the design, but the fixture engine advertises coverage the
  dataset cannot fulfil.

---

## 6. Test results and coverage gaps

### Results (re-run during this audit)

- `python -m pytest` → 78 passed (11.2 s).
- `python -m ruff check .` → clean; `ruff format --check .` → clean.
- `npm test` (Vitest) → 24 passed (2 files).

### What is covered well

- Critical resolutions: `gehen/ging/gegangen/Häusern → correct lexeme`
  (integration + unit).
- Match-type classification (`form` vs `normalized`), `queryType` null case,
  definition match, fuzzy-only-when-empty, limit, missing/empty query → 422.
- Ranker: priority vs frequency, ties deterministic, morph-certainty,
  similarity, limit, context merge.
- Cache key: case sensitivity, stability, whitespace, limit/engine variation.
- DB: unique constraints, cascades, aggregate contents, relations both
  directions, cross-corpus best frequency, example offsets, non-searchable
  forms excluded from the lookup index.
- Import: raw file untouched, deterministic processed output, trimming,
  derived lemma form, validation errors with locations, unknown relation/form
  and unknown frequency lemma error reporting, UTF-8 unescaped output.
- Frontend: formatting/labels, highlight slicing, result-card rendering and
  the "unsichere Analyse" flag.

### Gaps

- **No test exercises the real spaCy engine in CI unless the model is
  installed** (`test_morphology_adapter.py` skips it). The Docker path is the
  only place it is assured.
- **No test covers the PostgreSQL FTS / `pg_trgm` paths** — every test uses
  SQLite fallbacks. The production search backend is unverified by the suite.
- **No performance/regression guard** on engine construction or search latency
  (the P1-1 class of bug is invisible to the suite).
- **No test of the NFD/Unicode-equivalence case** (P2-1).
- **No test of the definition stage's precision behaviour** beyond the single
  `funktionieren` assertion — the test effectively enshrines the noisy
  behaviour.
- Cache **hit** path is not integration-tested with a live Redis (only the key
  function is unit-tested); the Docker stack was the only place it was
  exercised.
- No tests for `scripts.maintenance.rebuild_lookups`, `scripts.seed --reset`,
  or `scripts.schema` fallback behaviour.
- Frontend: no tests for the index page search flow, debouncing/race handling,
  entry page rendering, or accessibility; no Nuxt page/E2E tests.
- No end-to-end test that the web app's requests actually satisfy the API
  contract (types are mirrored manually, not generated).

---

## 7. Data licensing considerations

- **No third-party data is bundled.** The only data in the repo is
  hand-authored fixture JSON, and the project itself is MIT
  (`pyproject.toml`, `README.md`). There is nothing to mis-license today.
- `data/raw/README.md` correctly defines the rules for future sources:
  source name/URL, exact license, attribution text, redistribution terms and
  transformation notes; and it states that sources whose license forbids
  redistribution of derived data must not be committed.
- Gaps to close **before** adding real sources:
  - There is no machine-readable `MANIFEST.json` schema/validator yet — the
    README describes one but nothing enforces it (the importer accepts any
    correctly-shaped JSON and does not attach provenance).
  - Imported records carry an optional free-text `source` on examples only;
    lexemes/senses have **no provenance column**, so once real data is loaded
    there is no per-lexeme attribution trail. `README.md` attribution for
    bundled sources does not exist.
  - Common German dictionary sources (e.g. Wiktionary/DBnary, FreeDict,
    DWDS) have share-alike/attribution terms; the current schema cannot store
    the required notices. This is a **licensing prerequisite** for the next
    milestone, not a defect in this one.
- Recommendation: keep the MIT code license separate from a future data
  license file, and record per-source attribution at least at dataset level
  before ingesting anything real.

---

## 8. Prioritized recommendations

Ordering chosen so each step unblocks trustworthy work on real data.

### P1 — before real data / production

1. **Cache the morphology engine process-wide** (P1-1). Make
   `get_morphology_engine()` an `lru_cache`/singleton like `_response_cache_singleton`,
   so the spaCy model loads once per worker. Expected effect: parse/search drop
   from ~1–2 s to milliseconds and the response cache becomes meaningful.
2. **Add a relevance gate to the definition stage** (P1-2). Examples: a
   minimum `ts_rank`/similarity, a stopword/min-length guard, and/or skip
   definitions when a `lemma`/`form`/`normalized` candidate already exists
   (mirroring the fuzzy gate). Keep the stage's results labelled `definition`.

### P2 — robustness / correctness

3. Compare the **NFC-normalized** query (not the raw string) in
   `ExactSurfaceStage` so canonically-equivalent input keeps `matchType=form`
   (P2-1).
4. Reconcile the **SQLite vs PostgreSQL search semantics** (P2-2): align the
   fuzzy cutoff scales or document them as intentionally different; make the
   substring fallback case-insensitive on both dialects; decide policy when
   `pg_trgm`/FTS is absent (e.g. verify extension at startup and warn loudly).
5. Add a **DB-level uniqueness constraint on lexeme identity**
   `(language, normalized_lemma, part_of_speech)` (P2-3). The loader is
   already deterministic; the constraint protects against future non-loader
   writes.
6. Re-sync or scope the **fixture morphology engine** to the fixture dictionary
   (P2-4), or document the deliberate superset.
7. Add **PostgreSQL-path tests** (FTS + pg_trgm) — e.g. a CI job against a
   Postgres service — so the production search backend is covered (Section 6).

### P3 — polish / docs

8. Fix documentation drift (P3-2): `docs/data-model.md` `gender` values include
   `plural` (enum has none) and `form_type` lists `past` (enum uses
   `inflected`); relation types list `hyponym`/`hyperonym` (enum has neither);
   `docs/morphology.md` claims spaCy tagger probability for confidence
   (hard-coded 1.0); `docs/search.md` implies definition similarity feeds
   ranking (it does not). `apps/web/app/utils/format.ts` still carries unused
   `hyponym`/`hyperonym`/`plural` labels.
9. Add `python -m scripts.seed` to the API image `CMD` (or a documented entry
   point) so the image is self-sufficient outside Compose (P3-3).
10. Extend the default `CORS_ORIGINS` to match `.env.example`
    (`…:3000,http://127.0.0.1:3000,…:5173`) and document the mismatch (P3-4).
11. Add pagination/offset to `/api/search` (or document `limit ≤ 50` as the
    deliberate cap) (P3-5).
12. `updated_at` has no `onupdate`; either maintain it or drop it (P3-1).
13. Add a machine-readable source manifest + dataset-level attribution file
    before importing real data (Section 7).

---

## Findings register

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| P1-1 | P1 | Morphology engine (spaCy model) rebuilt per request | `deps.py:22`, `factory.py:47`, live timings |
| P1-2 | P1 | Definition stage unconditional, no relevance gate | `definition.py:17`, `pipeline.py:74`, probes |
| P2-1 | P2 | NFC/NFD input downgraded `form`→`normalized` | `surface.py:28`, NFD probe |
| P2-2 | P2 | SQLite vs PostgreSQL fuzzy/definition semantics diverge; extension not guaranteed | `search_repos.py:28-29`, migration-only extension |
| P2-3 | P2 | No DB uniqueness on `(language, normalized_lemma, part_of_speech)` | `orm/models.py:39-55` |
| P2-4 | P2 | Fixture engine covers lexemes absent from fixture dictionary | `fixture_engine.py`, `dictionary.json` |
| P3-1 | P3 | `updated_at` never updates | `orm/models.py:53` |
| P3-2 | P3 | Doc/code drift (gender, form_type, relations, confidence, similarity) | `docs/*.md`, `domain/enums.py` |
| P3-3 | P3 | API image `CMD` lacks seeding | `apps/api/Dockerfile:16` |
| P3-4 | P3 | CORS defaults inconsistent / `127.0.0.1` blocked | `config.py:18`, `.env.example:18`, compose |
| P3-5 | P3 | No search pagination (hard `limit ≤ 50`) | `routers/search.py:20` |

## Explicitly out of scope (per instructions)

- No product features added; no working component rewritten; no schema or
  behaviour changes; no data deleted or downloaded; no secrets exposed.
- Defects are documented only — the P1 issues were **not** fixed here.
- The next milestone was not started.
