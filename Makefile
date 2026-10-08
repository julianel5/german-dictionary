# Convenience commands. On Windows without Make, use the equivalents
# documented in README.md instead.

.PHONY: dev infra api web seed test test-api test-web lint format migrate

dev:            ## Start full stack via Docker Compose
	docker compose up -d --build

infra:          ## Start only PostgreSQL + Redis
	docker compose up -d db redis

api:            ## Run the API locally (requires DATABASE_URL or falls back to SQLite)
	python -m scripts.run_api

web:            ## Run the Nuxt dev server
	cd apps/web && npm run dev

seed:           ## Seed the database with the fixture dataset
	python -m scripts.seed

migrate:        ## Apply database migrations
	alembic -c apps/api/alembic.ini upgrade head

test:           ## Run backend + frontend tests
	python -m pytest
	cd apps/web && npm test

test-api:
	python -m pytest

test-web:
	cd apps/web && npm test

lint:           ## Lint backend + frontend
	ruff check .
	cd apps/web && npm run lint

format:         ## Format backend + frontend
	ruff format .
	ruff check --fix .
	cd apps/web && npm run format
