# Getting Started

This guide walks you from a fresh install to your first passing architecture check
in about five minutes.

## Prerequisites

- Python **3.12** or newer
- A project that uses `pyproject.toml`

## Installation

```bash
pip install pyarchrules
```

Verify:

```bash
pyarchrules --help
```

---

## Step 1 — Initialize configuration

Run from your project root (where `pyproject.toml` lives):

```bash
pyarchrules init-project
```

This adds a `[tool.pyarchrules]` section with sensible defaults:

```toml
[tool.pyarchrules]
project_name    = "myapp"
description     = "Architecture rules for this project"
root            = "."
strict          = true
validate_paths  = true
fail_on_warning = false
```

---

## Step 2 — Add a service

A *service* is any directory you want to enforce rules on.

```bash
pyarchrules add-service backend src/backend
```

Adds to `pyproject.toml`:

```toml
[tool.pyarchrules.services.backend]
path = "src/backend"
```

---

## Step 3 — Define rules

```toml
[tool.pyarchrules.services.backend]
path = "src/backend"

# Required directories
tree = ["api", "domain", "infra"]

# No extra directories allowed
tree_strict = true

# Import direction rules
dependencies = ["api -> domain", "domain -> infra"]
```

---

## Step 4 — Run the check

```bash
pyarchrules check
```

**Passing:**

```
🔍 Checking 1 service(s)...

📦 backend
   Path: src/backend
   Rules: tree_structure, internal_dependencies

✨ All checks passed!
   Checked 2 rule(s) across 1 service(s)
```

**Failing:**

```
❌  Validation failed!

Found 1 error(s) and 0 warning(s):

❌ [backend] tree_structure
   Missing required paths: ['domain']
```

---

## Step 5 — Add to CI

```yaml
- name: Architecture check
  run: pyarchrules check
```

Exit code `1` is returned on any violation when `strict = true`.

---

## Using the Python API

```python
# tests/test_architecture.py
from pyarchrules import PyArchRules

def test_architecture():
    rules = PyArchRules()
    rules.for_service("backend").must_contain_folders(["api", "domain", "infra"])
    rules.validate()  # raises PyArchError on violation
```

---

## Next Steps

- [Configuration](configuration.md)
- [CLI Reference](cli.md)
- [Python DSL](dsl.md)
- [Use Cases](use-cases.md)