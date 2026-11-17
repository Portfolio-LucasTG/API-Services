.DEFAULT_GOAL := help
SHELL := /bin/bash

HAS_FRONTEND := $(wildcard frontend/package.json)
TEST_DATABASE_URL ?= postgresql+psycopg://iris:iris@localhost:5432/iris_test

.PHONY: help setup format lint typecheck test test-integration check up down logs smoke clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

setup: ## Install Python + frontend deps and git hooks
	uv sync --all-packages
	uv run pre-commit install
ifneq ($(HAS_FRONTEND),)
	npm --prefix frontend ci
endif

format: ## Auto-format and auto-fix
	uv run ruff format .
	uv run ruff check --fix .
ifneq ($(HAS_FRONTEND),)
	npm --prefix frontend run format
	npm --prefix frontend run lint -- --fix
endif

lint: ## Lint without changing files
	uv run ruff check .
	uv run ruff format --check .
ifneq ($(HAS_FRONTEND),)
	npm --prefix frontend run lint
	npm --prefix frontend run format:check
endif

typecheck: ## Static type checks
	uv run mypy
ifneq ($(HAS_FRONTEND),)
	npm --prefix frontend run type-check
endif

test: ## Unit tests (no database needed)
	uv run pytest -m "not integration"
ifneq ($(HAS_FRONTEND),)
	npm --prefix frontend run test:unit
endif

test-integration: ## Integration tests against the db container
	docker compose up -d --wait db
	TEST_DATABASE_URL=$(TEST_DATABASE_URL) uv run pytest -m integration --cov-fail-under=0

check: lint typecheck test ## Everything that must pass before a commit

up: ## Build and start the whole stack
	docker compose up -d --build --wait

down: ## Stop the stack (keeps the volume)
	docker compose down

logs: ## Follow logs
	docker compose logs -f

smoke: ## End-to-end check against the running stack
	curl -fsS http://localhost:5000/health
	curl -fsS "http://localhost:5000/iris/setosa?page=1" | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["total"]==50 and len(d["items"])==10, d'
	curl -fsS http://localhost:8080/ > /dev/null
	curl -fsS "http://localhost:8080/api/iris/virginica/150" > /dev/null
	@echo "smoke OK"

clean: ## Remove caches
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
