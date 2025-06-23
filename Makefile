# Makefile for simple-sqlalchemy

.PHONY: help install install-dev test test-cov test-fast test-integration clean lint format type-check

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install package dependencies"
	@echo "  install-dev  - Install package with development dependencies"
	@echo "  test         - Run all tests"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  test-fast    - Run tests excluding slow tests"
	@echo "  test-integration - Run only integration tests"
	@echo "  clean        - Clean up build artifacts and cache"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with black and isort"
	@echo "  type-check   - Run type checking with mypy"

# Installation targets
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pip install -r tests/requirements.txt

# Test targets
test:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ -v \
		--cov=simple_sqlalchemy \
		--cov-report=term-missing \
		--cov-report=html:htmlcov \
		--cov-report=xml:coverage.xml

test-fast:
	python -m pytest tests/ -v -m "not slow"

test-integration:
	python -m pytest tests/test_integration.py -v

# Code quality targets
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	black --check simple_sqlalchemy/ tests/
	isort --check-only simple_sqlalchemy/ tests/

format:
	black simple_sqlalchemy/ tests/
	isort simple_sqlalchemy/ tests/

type-check:
	mypy simple_sqlalchemy/

# Development workflow
dev-setup: install-dev
	pre-commit install

dev-test: format lint type-check test-cov

# CI targets
ci-test:
	python -m pytest tests/ \
		--cov=simple_sqlalchemy \
		--cov-report=xml:coverage.xml \
		--cov-report=term

# Database targets
test-sqlite:
	python -c "from tests.conftest import *; import tempfile; db = DbClient('sqlite:///:memory:'); CommonBase.metadata.create_all(db.engine); print('SQLite test successful')"
