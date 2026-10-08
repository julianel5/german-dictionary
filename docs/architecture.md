# Architecture

## Purpose

This repository is the foundation of an open-source German dictionary and
language-learning platform: a fast, ad-free dictionary for learners. The
current milestone implements the dictionary **core** — lexical data model,
staged search pipeline, morphology abstraction, import pipeline, REST API and
a minimal Nuxt web UI. Accounts, SRS, browser extensions, audio, payments and
cloud infrastructure are explicitly out of scope.

The project is *inspired by* the architecture and product philosophy of
[Jiten](https://github.com/Sirush/Jiten) but contains no Jiten source code
and is not a fork.

## Implementation plan (this milestone)

1. Monorepo scaffold: `apps/api` (FastAPI), `apps/web` (Nuxt 4),
   `services/morphology` (Python package), `packages/shared-types` (TS),
   `scripts` (import/seed/maintenance), `data`, `tests`, `docs`.
2. Relational schema (SQLAlchemy 2.x + Alembic) separating lexeme, sense,
   word form, morphological features, lookup index, frequency, lexical
   relations and example sentences.
3. `german_morphology` package: `MorphologyEngine` protocol, spaCy-based
   German implementation (`de_core_news_sm`), deterministic fixture engine
   for tests, engine factory.
4. Search service with independent stages: normalize → exact surface →
   exact lemma → morphology → definition (FTS) → fuzzy (trigram) → rank →
   build response. Dialect-aware definition/fuzzy backends (PostgreSQL
   `to_tsvector` / `pg_trgm`, with SQLite fallbacks used by local tests).
5. REST API endpoints backed by repositories (no SQL in route handlers).
6. Import pipeline: `data/raw/` → importer → normalization/validation →
   `data/processed/` → PostgreSQL/SQLite. Fixture dataset + deterministic
   `python -m scripts.seed`.
7. Nuxt 4 dictionary UI (search box, result cards, entry page).
8. Tests: pytest unit + integration; Vitest for frontend utilities.

## Repository layout

```
apps/
  api/                 FastAPI application package (`app`), Alembic, Dockerfile
  web/                 Nuxt 4 application, Dockerfile
packages/
  shared-types/        TypeScript DTOs shared between web and future clients
services/
  morphology/          `german_morphology` Python package (MorphologyEngine)
scripts/               seed, importers, maintenance entry points
data/
  raw/                 raw source data (never modified in place)
  processed/           normalized/validated import output
  fixtures/            tiny offline dataset used by seed + tests
tests/                 pytest unit (search/morphology/db) + api integration
docs/                  architecture, data model, search, morphology
docker-compose.yml     postgres + redis + api + web for local development
```

## Component diagram

```
┌────────────┐   HTTP/JSON   ┌──────────────────────────────────────────┐
│  apps/web  │ ────────────► │  apps/api (FastAPI)                      │
│  Nuxt 4    │               │  routers → services → repositories       │
└────────────┘               └───────┬──────────────────┬───────────────┘
                                     │                  │
                              ┌──────▼──────┐    ┌──────▼───────────────┐
                              │ PostgreSQL  │    │ german_morphology    │
                              │ (+ Redis    │    │ MorphologyEngine     │
                              │  optional)  │    │  ├─ SpacyEngine      │
                              └─────────────┘    │  └─ FixtureEngine    │
                                                 └──────────────────────┘
 data/raw/ → scripts/import/ → data/processed/ → DB loader → PostgreSQL
```

## Key decisions

- **Single Python project.** One root `pyproject.toml` installs three
  importable packages: `app` (API), `german_morphology`, `scripts`.
- **Domain vs. DTO.** ORM rows are mapped to plain domain dataclasses
  (`app/domain`) before services build Pydantic response DTOs
  (`app/schemas`). Routers never issue SQL.
- **Morphology is a replaceable adapter.** Only `german_morphology` talks
  to spaCy; the API depends on the `MorphologyEngine` protocol only.
  Engine choice is a runtime setting (`MORPHOLOGY_ENGINE`).
- **Dialect-aware search backends.** Definition search uses PostgreSQL
  full-text search and fuzzy search uses `pg_trgm` in production; for
  local/hermetic tests the same repository interfaces degrade to
  `ILIKE`/`difflib` on SQLite. No hosted search services.
- **SQLite fallback for zero-setup development.** When `DATABASE_URL` is
  unset the API uses `data/dev.db`. Docker Compose provides PostgreSQL,
  Redis and the production-shaped stack.
- **Deterministic ranking.** Ranking is an explicit scoring function over
  (match type, morphological certainty, frequency), with stable
  tie-breakers; no random or time-dependent ordering.
- **Verified dependency choice for morphology.** DEMorphy (the
  originally considered library) is not installable from PyPI anymore —
  the name hosts a JetBrains dependency-confusion stub; the real project
  is an unmaintained GitHub repo requiring a manual dictionary download.
  spaCy's `de_core_news_sm` was verified to correctly lemmatize
  *ging/gingen/gegangen → gehen* and *Häusern → Haus* (see
  `docs/morphology.md`).

## Out of scope (future milestones)

Accounts/auth, spaced repetition, word lists, audio, CEFR metadata,
browser extension, public API keys, compound segmentation beyond stored
relations, hosted search (Elasticsearch/OpenSearch), cloud deployment.
