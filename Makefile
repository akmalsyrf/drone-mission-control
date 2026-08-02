.PHONY: help install up down logs backend frontend test lint typecheck fmt bootstrap

PYTHON ?= python3.12
VENV := backend/.venv
PY := $(VENV)/bin/python

help:
	@echo "Drone Mission Control"
	@echo "  make bootstrap  - copy .env.example, create venv, install deps"
	@echo "  make up         - start full stack (Docker Compose)"
	@echo "  make down       - stop stack"
	@echo "  make logs       - follow compose logs"
	@echo "  make backend    - run API locally (needs postgres/redis)"
	@echo "  make frontend   - run Vite dev server"
	@echo "  make test       - backend unit tests"
	@echo "  make lint       - ruff + frontend typecheck"
	@echo "  make typecheck  - mypy + tsc"

bootstrap:
	@test -f .env || cp .env.example .env
	@command -v $(PYTHON) >/dev/null 2>&1 || (echo "Missing $(PYTHON). Install Python 3.12+ or set PYTHON=python3"; exit 1)
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e "./backend[dev]"
	cd frontend && npm install
	@echo "Bootstrap complete. Activate with: source backend/.venv/bin/activate"

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

backend:
	cd backend && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && .venv/bin/pytest -q

lint:
	cd backend && .venv/bin/ruff check app tests
	cd frontend && npm run typecheck

typecheck:
	cd backend && .venv/bin/mypy app
	cd frontend && npm run typecheck

fmt:
	cd backend && .venv/bin/ruff check --fix app tests
	cd backend && .venv/bin/ruff format app tests
