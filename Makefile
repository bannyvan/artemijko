SHELL := /usr/bin/bash

.PHONY: migrate alembic-revision up down test backend-dev frontend-dev openapi

migrate:
	docker compose exec api alembic upgrade head

alembic-revision:
	docker compose exec api alembic revision --autogenerate -m "manual"

up:
	docker compose up -d --build

down:
	docker compose down -v

test:
	docker compose exec api pytest -q

backend-dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend-dev:
	cd frontend && pnpm dev --host

openapi:
	curl -s http://localhost:8000/openapi.json -o openapi.json && echo "Saved openapi.json"