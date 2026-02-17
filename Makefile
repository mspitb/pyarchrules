.PHONY: lint format test clean help

help:
	@echo "Available commands:"
	@echo "  make lint      - Run code quality checks (black, isort, ruff)"
	@echo "  make format    - Auto-format code with black and isort"
	@echo "  make test      - Run all tests"
	@echo "  make clean     - Remove build artifacts and cache"

lint:
	uv run black --check .
	uv run isort --check-only .
	uv run ruff check .

format:
	uv run black .
	uv run isort .
	uv run ruff check --fix .

test:
	uv run pytest tests/

clean:
	rm -rf dist/ build/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

