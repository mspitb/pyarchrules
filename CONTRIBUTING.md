# Contributing

Thank you for your interest in contributing to PyArchRules.

## Before you start

- For bug fixes and small improvements, open a pull request directly.
- For larger changes or new features, open an issue first to discuss the approach.

## Setup

```bash
git clone https://github.com/mspitb/pyarchrules
cd pyarchrules
uv sync --all-extras
```

## Running tests

```bash
make test
```

All tests must pass before a pull request will be reviewed.

## Linting

```bash
make lint    # check
make format  # auto-fix
```

## Pull request checklist

- [ ] Tests added or updated for the change
- [ ] All tests pass (`make test`)
- [ ] No lint errors (`make lint`)
- [ ] Docstrings updated if public API changed
- [ ] `CHANGELOG.md` updated with a short description under `Unreleased`

## Project structure

```
src/pyarchrules/
  cli.py                 # Typer CLI commands
  pyarchrules.py         # PyArchRules public class
  core/
    config.py            # pyproject.toml read/write
    spec_loader.py       # parses TOML into model objects
    registries/          # DSLRegistry, LinterRegistry
    rules/
      dsl/               # Python DSL rule implementations
      linter/            # TOML-driven rule implementations
      base/              # shared base classes
      checks/            # low-level file/import scanners
  model/
    spec/                # ProjectSpec, ServiceSpec
    rules/               # RuleViolation, RuleEvalResult
tests/
  cli/                   # CLI integration tests
  unit/                  # unit tests per rule and component
    dsl/                 # DSL rule unit tests
```

## License

By contributing you agree that your changes will be released under the [MIT License](LICENSE).

