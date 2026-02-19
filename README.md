<p align="center">
  <img src="https://gist.githubusercontent.com/mspitb/862bc8c4b0e176e98f06e624761519da/raw/f4237236769bd2739132790f6c6f1157e3be5131/pyarchrules_logo.svg" alt="PyArchRules Logo" width="600">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"></a>
</p>


## Features

- 🏗️ **Structure validation** - enforce directory tree requirements
- 🔗 **Dependency rules** - control module imports (e.g., `api -> domain`)
- 🎯 **DSL & Config** - use Python DSL or TOML configuration
- 🚀 **Zero setup** - works with `pyproject.toml`
- 🔍 **CLI & API** - integrate into CI/CD or use programmatically

## Installation

```bash
pip install pyarchrules
```

## Quick Start

```bash
# Initialize
pyarchrules init-project

# Check architecture
pyarchrules check
```

## Configuration Example

```toml
[tool.pyarchrules]
project_name = "myapp"

[tool.pyarchrules.services.backend]
path = "src/backend"

# Enforce directory structure
tree = ["api", "domain", "infra"]
tree_strict = true

# Control dependencies (api can import from domain)
dependencies = ["api -> domain", "domain -> infra"]
```

## Python API

```python
from pyarchrules import PyArchRules

rules = PyArchRules()

# DSL validation
rules.for_service("backend") \
    .must_contain_folders(["api", "domain"])

result = rules.validate()
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `pyarchrules init-project` | Initialize configuration |
| `pyarchrules check` | Validate architecture |
| `pyarchrules add-service NAME PATH` | Add service |
| `pyarchrules list-services` | List all services |

## Use Cases

**Monorepos** - enforce boundaries between services
```toml
[tool.pyarchrules.services.auth]
path = "services/auth"
dependencies = ["auth -> shared"]
```

**Clean Architecture** - validate layer dependencies
```toml
dependencies = [
    "api -> application",
    "application -> domain"
]
```

**Microservices** - ensure consistent structure
```toml
tree = ["api", "domain", "infrastructure"]
tree_strict = true
```

## Development

```bash
uv pip install -e ".[dev]"
make test
make lint
```

## Status

⚠️ **Alpha** - API may change before 1.0 release

## License

MIT

