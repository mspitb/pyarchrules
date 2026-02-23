.PHONY: lint format test clean help

help:
	@echo "Available commands:"
	@echo "  make lint      - Run ruff linter and format check"
	@echo "  make format    - Auto-format code with ruff"
	@echo "  make test      - Run all tests"
	@echo "  make clean     - Remove build artifacts and cache"

lint:
	uv run ruff check src/
	uv run ruff format --check src/

format:
	uv run ruff format src/
	uv run ruff check --fix src/

test:
	uv run pytest tests/

clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
