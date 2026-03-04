# Contributing

Thank you for your interest in contributing to PyArchRules.

## Before you start

- For bug fixes and small improvements, open a pull request directly.
- For larger changes or new features, open an issue first to discuss the approach.

## Setup

```bash
git clone https://github.com/mspitb/pyarchrules
cd pyarchrules
uv sync
```

This creates a virtual environment under `.venv/` and installs all dependencies including dev tools.

## Available commands

| Command | Description |
|---------|-------------|
| `make test` | Run all tests |
| `make lint` | Check code with ruff |
| `make format` | Auto-fix formatting and lint issues |
| `make clean` | Remove build artifacts and cache |

## Running tests

```bash
make test
# or directly:
uv run pytest tests/
```

All tests must pass before a pull request will be reviewed.

## Linting

```bash
make lint    # check only
make format  # auto-fix
```

## Docs

Documentation lives in `docs/docs/`. To preview locally:

```bash
cd docs
uv run mkdocs serve
```

The site is deployed automatically to [mspitb.github.io/pyarchrules](https://mspitb.github.io/pyarchrules/) on push to `main`.

## Pull request checklist

- [ ] Tests added or updated for the change
- [ ] All tests pass (`make test`)
- [ ] No lint errors (`make lint`)
- [ ] Docstrings updated if public API changed
- [ ] `docs/docs/changelog.md` updated with a short description under the latest version

## Project structure

```
src/pyarchrules/
  cli.py                 # Typer CLI commands
  pyarchrules.py         # PyArchRules public class
  core/
    config.py            # pyproject.toml read/write
    spec_loader.py       # parses TOML into ProjectSpec / ServiceSpec
    registries/          # DSLRegistry, LinterRegistry
    rules/
      dsl/               # Python DSL rule implementations
      linter/            # TOML-driven rule implementations (TreeRule, etc.)
      base/              # shared base classes
      checks/            # low-level file/import scanners
  model/
    spec/                # ProjectSpec, ServiceSpec, TreeMode
    rules/               # RuleViolation, RuleEvalResult
tests/
  cli/                   # CLI integration tests
  unit/                  # unit tests per rule and component
    dsl/                 # DSL rule unit tests
docs/
  docs/                  # Markdown source pages
  mkdocs.yml             # MkDocs configuration
```

## License

By contributing you agree that your changes will be released under the [MIT License](LICENSE).
