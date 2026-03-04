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

**PyArchRules** enforces architecture rules in Python projects:

- 🏗️ Folder structure validation per service
- 🔗 Internal dependency direction control
- 🛡️ Cross-service import isolation for monorepos
- 🐍 Python DSL for writing rules inside your test suite
- ⚙️ Zero extra config — everything in `pyproject.toml`
- 🚀 CI-ready — exit code `1` on any violation

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
root             = "."
validate_paths   = true
isolate_services = true

[tool.pyarchrules.services.backend]
path         = "src/backend"
tree         = ["api", "domain", "infra"]
tree_mode    = "strict"
dependencies = ["api -> domain", "domain -> infra", "* -> utils"]
```

## Python DSL

```python
# tests/test_architecture.py
from pyarchrules import PyArchRules

def test_architecture():
    rules = PyArchRules()
    rules.for_service("backend") \
        .must_contain_folders(["api", "domain", "infra"], allow_extra=False) \
        .no_wildcard_imports() \
        .no_circular_imports()
    rules.validate()
```

## CLI commands

| Command | Description |
|---------|-------------|
| `init-project` | Initialise `[tool.pyarchrules]` in `pyproject.toml` |
| `add-service NAME PATH` | Register a service |
| `remove-service NAME` | Remove a service |
| `list-services` | Show all configured services |
| `check` | Validate architecture |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
