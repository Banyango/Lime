.PHONY: help install test test-cov lint format format-check type-check check clean build docs docs-serve pre-commit-install pre-commit-run prompts-init prompts-lock prompts-check

LIME_CMD = uv run python src/main.py

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package and development dependencies
	uv sync --all-groups

test:  ## Run tests with pytest
	uv run pytest

test-cov:  ## Run tests with coverage
	uv run pytest --cov=lime --cov-report=html --cov-report=term

lint:  ## Run linting with ruff
	uv run ruff check . --fix

format:  ## Format code with ruff
	uv run ruff format .

format-check:  ## Check code formatting without making changes
	uv run ruff format --check .

type-check:  ## Run type checking with mypy
	uv run mypy src

check: format-check lint type-check test  ## Run all checks (format, lint, type-check, test)

clean:  ## Clean up build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.pyo' -delete

build:  ## Build the package
	uv build

pre-commit-install:  ## Install pre-commit hooks
	uv run pre-commit install

pre-commit-run:  ## Run pre-commit hooks on all files
	uv run pre-commit run --all-files

docs:  ## Build documentation
	uv run mkdocs build

docs-serve:  ## Serve documentation locally
	uv run mkdocs serve

prompts-init: ## Initialize prompt integrity manifest
	$(LIME_CMD) prompts init

prompts-lock: ## Generate prompt lock file from manifest
	$(LIME_CMD) prompts lock

prompts-check: ## Verify tracked prompts against lock file
	$(LIME_CMD) prompts check
