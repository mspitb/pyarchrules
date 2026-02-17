<p align="center">
  <img src="https://gist.githubusercontent.com/mspitb/862bc8c4b0e176e98f06e624761519da/raw/f4237236769bd2739132790f6c6f1157e3be5131/pyarchrules_logo.svg" alt="PyArchRules Logo" width="600">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" height="18"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+" height="18"></a>
</p>

<p align="center">
  <strong>Define and enforce architectural rules for Python projects with ease.</strong><br>
  Perfect for monorepos, microservices, and maintaining clean architecture boundaries.
</p>

## Installation

```bash
pip install pyarchrules
```

## Quick Start

Initialize in your project:

```bash
pyarchrules init-project
```

This creates configuration in `pyproject.toml`:

```toml
[tool.pyarchrules]
project_name = "my-project"
description = "Architecture rules for this project"

[tool.pyarchrules.services]
root = "."
```

## CLI Commands

```bash
# Initialize project
pyarchrules init-project

# Add a service
pyarchrules add-service api services/api

# List services
pyarchrules list-services

# Remove a service
pyarchrules remove-service api
```

## Configuration

Define services in `pyproject.toml`:

```toml
[tool.pyarchrules]
project_name = "my-project"
description = "Architecture rules"

[tool.pyarchrules.services]
root = "."

[tool.pyarchrules.services.api]
path = "services/api"

[tool.pyarchrules.services.billing]
path = "services/billing"
```

## Python API

```python
from pyarchrules import PyArchRules

# Load configuration
rules = PyArchRules(".")

# Access services
print(rules.services)  # {'root': '.', 'api': 'services/api', ...}
```

## Development Status

⚠️ **Alpha Release** - API may change in future versions.

## Development

### Setup

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"
```

### Code Quality Tools

Using Make (recommended):

```bash
# Run all linters
make lint

# Auto-format code
make format

# Run tests
make test
```

## License

MIT

