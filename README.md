<p align="center">
  <img src="https://gist.githubusercontent.com/mspitb/862bc8c4b0e176e98f06e624761519da/raw/f4237236769bd2739132790f6c6f1157e3be5131/pyarchrules_logo.svg" alt="PyArchRules Logo" width="600">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"></a>
  <a href="https://github.com/mspitb/pyarchrules"><img src="https://img.shields.io/badge/status-beta%200.1.0b1-orange.svg" alt="Status: Beta"></a>
  <a href="https://mspitb.github.io/pyarchrules/"><img src="https://img.shields.io/badge/docs-mkdocs-blue.svg" alt="Documentation"></a>
</p>

> ⚠️ **Pre-release (beta).** APIs may change before the stable `1.0` release.

📚 **[Full Documentation](https://mspitb.github.io/pyarchrules/)** — Getting Started · Configuration · CLI Reference · Use Cases

**PyArchRules** is an architecture linter for Python. *Ruff lints lines. PyArchRules lints architecture.*

It ships **four focused rules**:

- 🏗️ **`tree_structure`** — required folder layout per service
- 🔗 **`dependencies`** — internal import direction (layer allow-list)
- 🔁 **`no_circular_imports`** — AST-based cycle detection
- 🚧 **`service_isolation`** — forbid cross-service imports (`shared = true` opts out)

Plus:

- ⚙️ One config — everything in `pyproject.toml`, 9 keys total. Or skip it entirely with `PyArchRules.from_services({...})`.
- 🐍 **Full DSL parity** — every per-service rule is also a fluent method, so your test suite can be the single source of truth
- 🧱 Zero heavy dependencies — only `tomlkit` and `typer`
- 🚀 CI-ready — predictable exit codes (`0` ok / `1` violations / `2` bad config)
- 📦 Machine-readable output (`--format json`) for CI integrations

## Installation

```bash
pip install pyarchrules
```

## Quick start

```bash
# 1. Add [tool.pyarchrules] to pyproject.toml
pyarchrules init-project

# 2. Register a service
pyarchrules add-service backend src/backend

# 3. Run the check
pyarchrules check
```

## TOML configuration

```toml
[tool.pyarchrules]
isolate_services = true             # forbid cross-service imports

[tool.pyarchrules.services.shared]
path   = "services/shared"
shared = true                       # importable by everyone

[tool.pyarchrules.services.backend]
path                = "src/backend"
tree                = ["api", "domain", "infra"]
tree_mode           = "strict"
dependencies        = ["api -> domain", "domain -> infra", "* -> utils"]
no_circular_imports = true
```

That's the complete v1 schema — nine keys, four rules. See
[Configuration](https://mspitb.github.io/pyarchrules/configuration/) for the
full reference.

## Python DSL

Use it instead of, or alongside, `pyproject.toml`:

```python
# tests/test_architecture.py
from pyarchrules import PyArchRules

def test_architecture():
    rules = PyArchRules()
    rules.for_service("backend") \
         .tree_structure(["api", "domain", "infra"], mode="strict") \
         .dependencies(["api -> domain", "domain -> infra"]) \
         .no_circular_imports()
    rules.validate()
```

Don't want a `[tool.pyarchrules]` table at all? Use `from_services`:

```python
rules = PyArchRules.from_services({"backend": "src/backend"})
rules.for_service("backend").no_circular_imports().validate()
```

The DSL covers all three per-service rules. `service_isolation` is
project-wide and therefore TOML-only.

## CLI commands

| Command | Description |
|---------|-------------|
| `init-project` | Initialise `[tool.pyarchrules]` in `pyproject.toml` |
| `add-service NAME PATH` | Register a service |
| `remove-service NAME` | Remove a service |
| `list-services` | Show all configured services |
| `show-config` | Dump the resolved config (JSON) for debugging |
| `check` | Validate architecture |

`check` supports `--config PATH`, `--service NAME`, `--rule NAME`,
`--warnings-as-errors`/`-W`, and `--format text|json`.

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Validation passed |
| `1` | At least one violation |
| `2` | Configuration error (bad `pyproject.toml`, unknown service filter, etc.) |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT

