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

Ruff is pinned in `pyproject.toml` so local formatting and CI use the same version.

## Docs

Documentation lives in `docs/docs/`. To preview locally:

```bash
make docs
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
    runner.py            # RuleRunner: runs rules, reports, raises
    reporting.py         # ViolationReporter implementations (text / json)
    rules/
      rule.py            # Rule base class (see "Adding a rule" in its docstring)
      dsl/base.py        # DslRule: interface for rules exposed in the Python DSL
      linter/base.py     # LinterRule: interface for rules enabled from TOML
      factory.py         # RuleFactory: ServiceSpec -> rules (TOML entry point)
      rule_set.py        # ServiceRuleSet: fluent DSL builder (DSL entry point)
      *_rule.py          # tree, dependencies, no_circular_imports, isolation
      checks/            # import scanning and cycle detection
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
