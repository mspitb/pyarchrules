# Python DSL

The Python DSL lets you express architecture rules directly in Python code,
typically inside your test suite. This gives you full language power —
loops, conditionals, parameterisation — and tight integration with pytest.

---

## Setup

```python
from pyarchrules import PyArchRules

# Discovers pyproject.toml by walking up from the current directory
rules = PyArchRules()
```

You can also pass an explicit path:

```python
rules = PyArchRules("/path/to/project")
```

Services must be registered in `[tool.pyarchrules.services]`.
The DSL layers additional in-code rules on top.

---

## `for_service(name)`

Entry point for attaching rules to a service. Returns a `ServiceRuleSet` for method chaining.

```python
rule_set = rules.for_service("backend")
```

Raises `PyArchError` if the service is not found in `pyproject.toml`.

---

## `must_contain_folders(folders, allow_extra=True)`

Assert that the service directory contains specific sub-folders.

```python
rules.for_service("backend").must_contain_folders(["api", "domain", "infra"])
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `folders` | list[str] | *(required)* | Folders that must exist in the service root. |
| `allow_extra` | bool | `True` | When `False`, unlisted folders are a violation. |

**Strict layout (no extra folders):**

```python
rules.for_service("backend").must_contain_folders(
    ["api", "domain", "infra"],
    allow_extra=False,
)
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

print(f"Errors:   {result.error_count}")
print(f"Warnings: {result.warning_count}")
print(f"Valid:    {result.is_valid}")

for v in result.violations:
    print(f"[{v.severity}] {v.service_name} / {v.rule_name}: {v.message}")
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `raise_on_violation` | bool | `True` | Raise `PyArchError` on violations. |
| `verbose` | bool | `True` | Print violation summary to stdout. |
| `reporter` | ViolationReporter or None | `None` | Custom reporter; defaults to `ConsoleViolationReporter`. |
| `run_dsl` | bool | `True` | Execute DSL rules. |
| `run_linter` | bool | `False` | Also run TOML-based tree and dependency rules. |

---

## Using the DSL in pytest

```python
# tests/test_architecture.py
import pytest
from pyarchrules import PyArchRules


@pytest.fixture(scope="session")
def arch():
    return PyArchRules()


def test_backend_structure(arch):
    arch.for_service("backend").must_contain_folders(["api", "domain", "infra"])
    arch.validate()


def test_shared_structure(arch):
    arch.for_service("shared").must_contain_folders(["models", "utils"])
    arch.validate()
```

---

## Combining DSL and linter rules

```python
rules.for_service("backend").must_contain_folders(["api", "domain"])

result = rules.validate(
    run_dsl=True,
    run_linter=True,
    raise_on_violation=False,
    verbose=False,
)

assert result.is_valid, "Violations:\n" + "\n".join(
    f"  {v.service_name}: {v.message}" for v in result.violations
)
```

---

## Inspecting services

```python
rules = PyArchRules()
print(rules.services)
# {'backend': 'src/backend', 'shared': 'services/shared'}
```

**Parameterised tests:**

```python
@pytest.mark.parametrize("service", ["catalog", "orders", "auth"])
def test_standard_layout(arch, service):
    arch.for_service(service).must_contain_folders(["api", "domain", "infra"])
    arch.validate()
```

---

## `RuleEvalResult`

| Attribute | Type | Description |
|-----------|------|-------------|
| `violations` | list[RuleViolation] | All violations collected. |
| `is_valid` | bool | `True` when there are no violations. |
| `error_count` | int | Number of `"error"` severity violations. |
| `warning_count` | int | Number of `"warning"` severity violations. |

---

## `RuleViolation`

| Attribute | Type | Description |
|-----------|------|-------------|
| `rule_name` | str | Identifier of the triggering rule. |
| `service_name` | str | Name of the affected service. |
| `severity` | str | `"error"` or `"warning"`. |
| `message` | str | Human-readable description. |
| `details` | dict or None | Machine-readable details (paths, module names, etc.). |

---

## Error handling

```python
from pyarchrules.core.errors import PyArchError

try:
    rules = PyArchRules()
    rules.for_service("nonexistent")
except PyArchError as e:
    print(f"Configuration error: {e}")
```

Common causes:

- `pyproject.toml` not found in the directory tree
- Service name not registered in `[tool.pyarchrules.services]`
- Validation failure when `raise_on_violation=True`

