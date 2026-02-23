# Python DSL

The Python DSL lets you express architecture rules directly in Python,
typically inside your test suite.

---

## Setup

```python
from pyarchrules import PyArchRules

# Discovers pyproject.toml by walking up from the current directory
rules = PyArchRules()

# Or pass an explicit path
rules = PyArchRules("/path/to/project")
```

Services must be registered in `[tool.pyarchrules.services]` in `pyproject.toml`.

---

## `for_service(name)`

Returns a `ServiceRuleSet` for method chaining. Raises `PyArchError` if the service
is not found in `pyproject.toml`.

```python
rules.for_service("backend").must_contain_folders(["api", "domain", "infra"])
```

---

## `validate()`

Runs all registered DSL rules and returns a `RuleEvalResult`.

```python
result = rules.validate()
```

By default raises `PyArchError` on any violation. To inspect programmatically:

```python
result = rules.validate(raise_on_violation=False, verbose=False)

for v in result.violations:
    print(f"[{v.severity}] {v.service_name} / {v.rule_name}: {v.message}")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `raise_on_violation` | bool | `True` | Raise `PyArchError` on violations. |
| `verbose` | bool | `True` | Print violation summary to stdout. |
| `reporter` | ViolationReporter or None | `None` | Custom reporter. |

---

## Rules reference

### `must_contain_folders(folders, allow_extra=True)`

Assert the service contains specific sub-folders.

```python
rules.for_service("backend").must_contain_folders(["api", "domain", "infra"])

# No extra folders allowed
rules.for_service("backend").must_contain_folders(
    ["api", "domain", "infra"], allow_extra=False
)
```

---

### `must_contain_files(files)`

Assert the service contains specific files.

```python
rules.for_service("backend").must_contain_files(["__init__.py", "README.md"])
```

---

### `no_wildcard_imports(folder=None)`

Forbid `from x import *` across the service or within a folder.

```python
rules.for_service("backend").no_wildcard_imports()
rules.for_service("backend").no_wildcard_imports("domain")
```

---

### `no_private_imports(folder=None)`

Forbid importing private names (`_name`) from other modules.

```python
rules.for_service("backend").no_private_imports()
rules.for_service("backend").no_private_imports("api")
```

---

### `no_relative_imports_in(folder=None)`

Forbid relative imports (`from . import …`) across the service or within a folder.

```python
rules.for_service("backend").no_relative_imports_in()
rules.for_service("backend").no_relative_imports_in("api")
```

---

### `no_circular_imports(folder=None)`

Detect circular import chains within the service or a folder.

```python
rules.for_service("backend").no_circular_imports()
rules.for_service("backend").no_circular_imports("domain")
```

---

### `layer_must_not_import(source, target)`

Assert that one folder never imports from another.

```python
rules.for_service("backend").layer_must_not_import("domain", "infra")
```

---

### `allowed_external_libs(folder=None, *, libs)`

Restrict a folder (or the whole service) to import only from an explicit allowlist
of third-party libraries. Relative imports, stdlib, and imports from other folders
within the same service are always allowed.

```python
rules.for_service("backend").allowed_external_libs(libs=["pydantic"])
rules.for_service("backend").allowed_external_libs("domain", libs=["pydantic"])
```

---

### `forbidden_external_libs(folder=None, *, libs)`

Forbid specific third-party libraries from being imported.

```python
rules.for_service("backend").forbidden_external_libs(libs=["django"])
rules.for_service("backend").forbidden_external_libs("domain", libs=["django", "flask"])
```

---

### `no_test_files_in(folder)`

Assert that a folder contains no test files (`test_*.py` or `*_test.py`).

```python
rules.for_service("backend").no_test_files_in("domain")
```

---

### `no_files_in_folder(folder)`

Assert that a folder contains no direct `.py` files — only sub-folders.

```python
rules.for_service("backend").no_files_in_folder("api")
```

---

### `max_depth(depth, folder=None)`

Limit the directory nesting depth.

```python
rules.for_service("backend").max_depth(3)
rules.for_service("backend").max_depth(2, folder="domain")
```

---

### `files_must_match_pattern(folder, pattern)`

Assert all files in a folder match a glob pattern.

```python
rules.for_service("backend").files_must_match_pattern("domain", "*_service.py")
```

---

### `files_must_be_snake_case(folder=None)`

Assert all Python file names use `snake_case`.

```python
rules.for_service("backend").files_must_be_snake_case()
rules.for_service("backend").files_must_be_snake_case("api")
```

---

### `classes_must_match_pattern(folder, pattern)`

Assert all class names in a folder match a regex pattern.

```python
rules.for_service("backend").classes_must_match_pattern("domain", r".*Service$")
rules.for_service("backend").classes_must_match_pattern("infra", r".*Repository$")
```

---

## Full example

```python
# tests/test_architecture.py
import pytest
from pyarchrules import PyArchRules


@pytest.fixture(scope="session")
def arch():
    return PyArchRules()


def test_backend_structure(arch):
    arch.for_service("backend") \
        .must_contain_folders(["api", "domain", "infra"], allow_extra=False) \
        .no_wildcard_imports() \
        .no_circular_imports() \
        .no_test_files_in("domain") \
        .classes_must_match_pattern("domain", r".*Service$")
    arch.validate()


@pytest.mark.parametrize("service", ["catalog", "orders", "auth"])
def test_standard_layout(arch, service):
    arch.for_service(service).must_contain_folders(
        ["api", "domain", "infra"], allow_extra=False
    )
    arch.validate()
```

---

## Result objects

### `RuleEvalResult`

| Attribute | Type | Description |
|-----------|------|-------------|
| `violations` | list[RuleViolation] | All violations collected. |
| `is_valid` | bool | `True` when there are no violations. |
| `error_count` | int | Number of `"error"` severity violations. |
| `warning_count` | int | Number of `"warning"` severity violations. |

### `RuleViolation`

| Attribute | Type | Description |
|-----------|------|-------------|
| `rule_name` | str | Identifier of the rule that triggered. |
| `service_name` | str | Name of the affected service. |
| `severity` | str | `"error"` or `"warning"`. |
| `message` | str | Human-readable description. |
| `details` | dict | Machine-readable context (paths, module names, etc.). |

