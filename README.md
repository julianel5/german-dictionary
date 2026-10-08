# Deutsch Wörterbuch — German Dictionary Core

A fast, ad-free German dictionary for language learners: an open-source
monorepo with a FastAPI search backend, a staged/multi-stage search
pipeline, a replaceable morphology engine and a Nuxt 4 web UI.

The design is *inspired by* the architecture and product philosophy of
[Jiten](https://github.com/Sirush/Jiten); this repository contains no
Jiten source code and is not a fork.

This milestone implements the **dictionary core only**: lexical data
model, import pipeline, REST API, search pipeline, web UI, tests and
docs. Accounts, spaced repetition, browser extensions, audio and hosted
search (Elasticsearch) are explicitly out of scope — see
[docs/architecture.md](docs/architecture.md).

## Repository layout

```
apps/api/             FastAPI application (`app` package) + Alembic migrations
apps/web/             Nuxt 4 web application (search + entry pages)
services/morphology/  `german_morphology` package (MorphologyEngine protocol)
packages/shared-types/ TypeScript DTOs shared between API and web
scripts/              seed, importers, maintenance entry points
data/fixtures/        tiny offline dataset (seed + tests + Docker)
data/raw/, processed/ import input/output (raw sources are never modified)
tests/                pytest unit + integration tests
docs/                 architecture, data model, search, morphology
```

## Quickstart (local, no Docker)

Requirements: Python 3.13, Node 24 (or 22.19+), npm.

```bash
# 1. install Python deps (one root project: app + german_morphology + scripts)
pip install -e ".[dev]"
python -m spacy download de_core_news_sm

# 2. seed the SQLite database (data/dev.db) with the fixture dataset
python -m scripts.seed

# 3. run the API on http://localhost:8000
python -m scripts.run_api

# 4. web app (second terminal)
cd apps/web
npm install
npm run dev            # http://localhost:3000
```

The API falls back to `data/dev.db` when `DATABASE_URL` is unset.
Point the web app at a different API with
`NUXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev`.

### Try it

```bash
curl "http://localhost:8000/api/search?q=gehen"        # lemma match
curl "http://localhost:8000/api/search?q=ging"         # inflected form -> gehen
curl "http://localhost:8000/api/search?q=gegangen"     # participle -> gehen
curl "http://localhost:8000/api/search?q=H%C3%A4usern" # dative plural -> Haus
curl "http://localhost:8000/api/parse?text=Ich%20ging%20nach%20Hause."
curl "http://localhost:8000/api/health"
```

## Tests and lint

```bash
# backend (pytest, hermetic SQLite + fixture morphology engine)
python -m pytest

# frontend (vitest + eslint + prettier)
cd apps/web
npm test
npm run lint
npm run format:check

# backend lint
ruff check .
ruff format --check .
```

## Database migrations

```bash
alembic -c apps/api/alembic.ini upgrade head   # apply
python -m scripts.maintenance.rebuild_lookups  # rebuild lookup index
```

`python -m scripts.seed` creates the schema automatically when the
database is empty (Alembic first, `create_all` fallback), then loads the
fixture dataset deterministically. `python -m scripts.seed --reset`
drops and reloads everything.

## Import pipeline

```bash
# data/raw/<source>  ->  normalize + validate  ->  data/processed/*.json  ->  DB
python -m scripts.import.import_dictionary --source data/fixtures/dictionary.json
python -m scripts.import.import_frequency   --source data/fixtures/frequency.json
```

Importers write to `data/processed/` only; raw sources are read-only.
The normalized record contract lives in `scripts/normalized.py`.

## Docker Compose (full stack)

```bash
docker compose up -d --build
# API:  http://localhost:8000   Web: http://localhost:3000
# PostgreSQL: localhost:5432    Redis: localhost:6379
```

Compose starts PostgreSQL, Redis, the API (seeds on boot) and the built
web app. The browser calls the API directly at
`NUXT_PUBLIC_API_BASE=http://localhost:8000`.

## Documentation

- [docs/architecture.md](docs/architecture.md) — components, key decisions, scope
- [docs/data-model.md](docs/data-model.md) — schema and relationships
- [docs/search.md](docs/search.md) — staged pipeline, ranking, match types
- [docs/morphology.md](docs/morphology.md) — engine protocol, spaCy/fixture engines

## License

MIT (fixture data provenance is documented in `data/raw/README.md`).
