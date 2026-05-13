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

This adds an empty `[tool.pyarchrules]` block to `pyproject.toml`. Service
definitions go under `[tool.pyarchrules.services.<name>]`.

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
tree_mode    = "strict"
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

Exit code `1` is returned on any error, `2` on a configuration problem
(missing `pyproject.toml`, malformed table, etc.). See
[CLI Reference → Exit codes](cli.md#exit-codes).

---

## 5. Inspect the resolved config

To see exactly which services and rules `check` will run — useful when
debugging a monorepo or a `--config` override:

```bash
pyarchrules show-config
```

Outputs a JSON document with every service, its declared keys, and the list
of rules that will actually execute.

---

## 6. CI integration

```yaml
- name: Architecture check
  run: pyarchrules check
```

For machine-readable output (GitHub annotations, custom dashboards):

```bash
pyarchrules check --format json --quiet > arch.json
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
         .tree_structure(["domain", "application", "infra"], mode="strict") \
         .dependencies(["application -> domain", "infra -> domain"]) \
         .no_circular_imports()
    rules.validate()
```

If you don't want a `[tool.pyarchrules]` table at all, use `from_services`
for a TOML-free setup:

```python
rules = PyArchRules.from_services({"backend": "src/backend"})
rules.for_service("backend").no_circular_imports().validate()
```

See [Python DSL](dsl.md) for all available rules.
