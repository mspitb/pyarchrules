<p align="center">
  <img src="https://gist.githubusercontent.com/mspitb/862bc8c4b0e176e98f06e624761519da/raw/f4237236769bd2739132790f6c6f1157e3be5131/pyarchrules_logo.svg" alt="PyArchRules Logo" width="500">
</p>

<p align="center">
  <a href="https://github.com/mspitb/pyarchrules/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"></a>
  <img src="https://img.shields.io/badge/status-beta%200.1.0b1-orange.svg" alt="Status: Beta">
</p>

# PyArchRules

**PyArchRules** enforces architecture rules in Python projects. Define folder layouts,
dependency directions, and service boundaries in `pyproject.toml` or in Python —
then run `pyarchrules check` in CI to catch violations automatically.

## Quick start

```bash
pip install pyarchrules
pyarchrules init-project
pyarchrules add-service backend src/backend
pyarchrules check
```

## What it does

| Feature | How |
|---------|-----|
| Folder structure | `tree`, `tree_strict` per service |
| Import direction | `dependencies = ["api -> domain"]` |
| Service isolation | `isolate_services = true` |
| Path validation | `validate_paths = true` |
| Python DSL | fluent API in your test suite |

## Pages

- [Getting Started](getting-started.md) — Install and run your first check.
- [Configuration](configuration.md) — All `[tool.pyarchrules]` options.
- [CLI Reference](cli.md) — Commands and flags.
- [Python DSL](dsl.md) — Write rules in Python.
