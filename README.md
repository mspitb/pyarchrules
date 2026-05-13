<p align="center">
  <img src="https://gist.githubusercontent.com/mspitb/862bc8c4b0e176e98f06e624761519da/raw/f4237236769bd2739132790f6c6f1157e3be5131/pyarchrules_logo.svg" alt="PyArchRules Logo" width="600">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"></a>
  <a href="https://github.com/mspitb/pyarchrules"><img src="https://img.shields.io/badge/status-beta%200.1.0b2-orange.svg" alt="Status: Beta"></a>
  <a href="https://mspitb.github.io/pyarchrules/"><img src="https://img.shields.io/badge/docs-mkdocs-blue.svg" alt="Documentation"></a>
</p>

# PyArchRules

**Architecture linter for Python.**

Define your project's folder structure and import rules in `pyproject.toml`
(or in Python) and enforce them in CI or from your test suite.

📚 **[Full documentation](https://mspitb.github.io/pyarchrules/)**

## Key features

- Folder structure validation.
- Directional dependency rules between modules.
- Isolation between services and layers.
- Circular import detection.

## Quick start

### 1. Install

```bash
pip install pyarchrules
```

### 2. Define your rules

**Option A — `pyproject.toml` (recommended)**

```toml
# pyproject.toml
[tool.pyarchrules.services.backend]
path = "src/backend"

# Required folder structure
tree      = ["api", "domain", "infra"]
tree_mode = "strict"                       # exists / strict / exact

# Allowed import directions
dependencies = [
    "api -> domain",
    "domain -> infra",
]

# Prevent circular imports
no_circular_imports = true
```

Run it:

```bash
pyarchrules check
```

**Option B — Python DSL (great for tests)**

```python
# tests/test_architecture.py
from pyarchrules import PyArchRules


def test_backend_architecture():
    rules = PyArchRules()
    (
        rules.for_service("backend")
             .tree_structure(["api", "domain", "infra"], mode="strict")
             .dependencies(["api -> domain", "domain -> infra"])
             .no_circular_imports()
    )
    rules.validate()
```

Run it:

```bash
pytest tests/test_architecture.py
```

## Next steps

- [Configuration](https://mspitb.github.io/pyarchrules/configuration/) — full `[tool.pyarchrules]` reference.
- [Python DSL](https://mspitb.github.io/pyarchrules/dsl/) — every rule available as a fluent method.
- [Use Cases](https://mspitb.github.io/pyarchrules/use-cases/) — monorepo and Clean Architecture patterns.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT

