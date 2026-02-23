# Getting Started

## Requirements

- Python 3.12+
- A project with `pyproject.toml`

## Installation

```bash
pip install pyarchrules
```

---

## 1. Initialise

Run from the directory that contains `pyproject.toml`:

```bash
pyarchrules init-project
```

This adds a `[tool.pyarchrules]` block with defaults:

```toml
[tool.pyarchrules]
project_name     = "myapp"
description      = "Architecture rules for this project"
root             = "."
validate_paths   = true
isolate_services = true
```

---

## 2. Add a service

A *service* is any directory you want to enforce rules on.

```bash
pyarchrules add-service backend src/backend
```

Appends to `pyproject.toml`:

```toml
[tool.pyarchrules.services.backend]
path = "src/backend"
```

---

## 3. Define rules

Edit `pyproject.toml` to add the rules you need:

```toml
[tool.pyarchrules.services.backend]
path         = "src/backend"
tree         = ["api", "domain", "infra"]
tree_strict  = true
dependencies = ["api -> domain", "domain -> infra", "* -> utils"]
```

See [Configuration](configuration.md) for the full list of options.

---

## 4. Run the check

```bash
pyarchrules check
```

**Passing:**

```
🔍 Checking 1 service(s)...

📦 backend  src/backend

✨ All checks passed!
   Checked 2 rule(s) across 1 service(s)
```

**Failing:**

```
❌  Validation failed!

Found 1 error(s):

❌ [backend] tree_structure
   Missing required paths: ['domain']
```

Exit code `1` is returned on any error.

---

## 5. CI integration

```yaml
- name: Architecture check
  run: pyarchrules check
```

---

## Python API

Rules can also be written in Python, typically inside pytest:

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

See [Python DSL](dsl.md) for all available rules.
