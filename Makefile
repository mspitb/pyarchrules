.PHONY: lint format test help docs

help:
	@echo "Available commands:"
	@echo "  make lint      - Run ruff linter and format check"
	@echo "  make format    - Auto-format code with ruff"
	@echo "  make test      - Run all tests"
	@echo "  make docs      - Serve the documentation locally"

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .
	uv run ruff check --fix .

test:
	uv run pytest tests/

docs:
	uv run mkdocs serve -f docs/mkdocs.yml -a "localhost:8888"