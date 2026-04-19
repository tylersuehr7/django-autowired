.PHONY: help install sync test test-injector test-lagom test-wireup test-dishka lint format typecheck cov docs docs-serve clean build

help:
	@echo "django-autowired — development commands"
	@echo ""
	@echo "  make install       Create venv and install in editable mode with dev extras"
	@echo "  make sync          Sync dependencies from pyproject.toml"
	@echo "  make test          Run the full test suite"
	@echo "  make test-injector Run only injector backend tests"
	@echo "  make test-lagom    Run only lagom backend tests"
	@echo "  make test-wireup   Run only wireup backend tests"
	@echo "  make test-dishka   Run only dishka backend tests"
	@echo "  make cov           Run tests with coverage report"
	@echo "  make lint          Run ruff"
	@echo "  make format        Auto-format with ruff"
	@echo "  make typecheck     Run mypy"
	@echo "  make docs          Build MkDocs site"
	@echo "  make docs-serve    Serve MkDocs site locally"
	@echo "  make build         Build wheel + sdist"
	@echo "  make clean         Remove build artifacts and caches"

install:
	uv sync --all-extras

sync:
	uv sync --all-extras

test:
	uv run pytest tests/

test-injector:
	uv run pytest tests/backends/test_injector.py tests/test_scopes.py

test-lagom:
	uv run pytest tests/backends/test_lagom.py

test-wireup:
	uv run pytest tests/backends/test_wireup.py

test-dishka:
	uv run pytest tests/backends/test_dishka.py

cov:
	uv run pytest --cov=src/django_autowired --cov-report=term-missing --cov-report=xml

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

typecheck:
	uv run mypy src

docs:
	uv run mkdocs build

docs-serve:
	uv run mkdocs serve

build:
	uv build

clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
