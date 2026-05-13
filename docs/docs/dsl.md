# Python DSL

The Python DSL lets you express architecture rules directly in Python,
typically inside your test suite. All three per-service rules
(`tree_structure`, `dependencies`, `no_circular_imports`) are available as
fluent methods on `ServiceRuleSet`, mirroring the `pyproject.toml` keys.

> **Project-level rules (TOML only).** `isolate_services` is a cross-service
> rule and the DSL is per-service, so it can only be configured in
> `pyproject.toml`. See
> [Configuration → Service isolation](configuration.md#service-isolation).

The CLI (`pyarchrules check`) runs only the TOML rules; your test suite runs
only the DSL rules.

---

## Setup

```python
from pyarchrules import PyArchRules

# Discovers pyproject.toml by walking up from the current directory
rules = PyArchRules()

# Or pass an explicit path (file inside the project, or the project root)
rules = PyArchRules("/path/to/project")
```

Services declared in `[tool.pyarchrules.services]` are available via
`for_service(...)`. If you don't want a TOML config at all, use
[`PyArchRules.from_services`](#config-less-usage).

---

## `for_service(name)`

Returns a `ServiceRuleSet` for method chaining. Raises `ServiceNotFoundError`
if the service is not declared (either in `pyproject.toml` or via
`from_services`).

```python
rules.for_service("backend") \
     .tree_structure(["domain", "application", "infrastructure"], mode="strict") \
     .dependencies(["application -> domain", "infrastructure -> domain"]) \
     .no_circular_imports()
```

---

## Config-less usage

`PyArchRules.from_services` builds an instance without requiring a
`[tool.pyarchrules]` table — useful when your test suite is the single source
of truth.

```python
from pathlib import Path
from pyarchrules import PyArchRules

rules = PyArchRules.from_services(
    {"backend": "src/backend", "frontend": "src/frontend"},
    project_root=Path(__file__).parent.parent,  # defaults to cwd
)

rules.for_service("backend").no_circular_imports()
rules.validate()
```

`PyArchRules.from_spec(spec, project_root=...)` is a power-user variant that
accepts a pre-built `ProjectSpec`.

---

## `validate()`

Runs all registered DSL rules and returns a `RuleEvalResult`.

```python
result = rules.validate()
```

By default raises `ValidationError` on any error-severity violation. To inspect
programmatically:

```python
result = rules.validate(raise_on_violation=False, verbose=False)

for v in result.violations:
    location = f" ({v.file}:{v.line})" if v.file else ""
    print(f"[{v.severity}] {v.service_name} / {v.rule_name}{location}: {v.message}")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `raise_on_violation` | bool | `True` | Raise `ValidationError` on errors. |
| `verbose` | bool | `True` | Forward the result to *reporter*. |
| `reporter` | `ViolationReporter` or `None` | `None` | Custom reporter; default writes to stderr. |

---

## `check_linter()`

Runs the rules declared in `pyproject.toml` (`tree_structure`, `dependencies`,
`no_circular_imports` when its TOML key is set). Defaults are inverted
compared to `validate()` so the CLI can format output itself:
`raise_on_violation=False`, `verbose=False`.

```python
result = rules.check_linter()
if not result.is_valid:
    for v in result.violations:
        ...
```

---

## Rules reference

All three per-service rules accept the same configuration shape as their
`pyproject.toml` counterparts and produce identical `RuleViolation` objects.
See [Configuration](configuration.md) for the underlying semantics of each
rule. (The project-wide `service_isolation` rule is TOML-only — see the
callout at the top of this page.)

### `tree_structure(tree, *, mode="exists", allow_files=True, ignore=None)`

Validate the service's directory layout.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tree` | `list[str]` | — | Required directory/file paths, relative to the service root. Duplicate entries raise `ConfigError`. |
| `mode` | `"exists"` \| `"strict"` \| `"exact"` | `"exists"` | Strictness — see [Configuration](configuration.md#strictness-levels). |
| `allow_files` | bool | `True` | In `strict`/`exact` mode, tolerate loose files. |
| `ignore` | `list[str]` or `None` | `None` | Glob patterns of directory basenames to skip in `strict`/`exact` mode (`["__snapshots__", "migrations_*"]`). |

```python
rules.for_service("backend").tree_structure(
    ["domain", "application", "infrastructure"],
    mode="strict",
    ignore=["__snapshots__", "migrations_*"],
)
```

Raises `ConfigError` if `mode` is not a valid `TreeMode`, or if `tree`
contains duplicate entries.

### `dependencies(rules)`

Constrain internal import flow within the service.

| Parameter | Type | Description |
|-----------|------|-------------|
| `rules` | `list[str]` | Strings using the same grammar as the TOML key, e.g. `"api -> domain"`. |

```python
rules.for_service("backend").dependencies([
    "application -> domain",
    "infrastructure -> domain",
    "* -> shared",
])
```

Strings are parsed eagerly; malformed syntax, `* -> *`, and invalid paths
raise `ConfigError` immediately. Overlapping rule pairs (e.g.
`"api -> domain"` + `"api/v1 -> domain"`) are reported at `validate()` time
as **warnings**, not errors — see
[Configuration → Overlapping rules](configuration.md#overlapping-rules-warning).

### `no_circular_imports(folder=None)`

Detect circular import chains within the service or a folder. Uses AST-based
DFS cycle detection.

```python
rules.for_service("backend").no_circular_imports()
rules.for_service("backend").no_circular_imports("domain")
```

---

## TOML + DSL coexistence

The two surfaces run independently:

- `pyarchrules check` (CLI) → only TOML-declared rules, via `check_linter()`.
- `validate()` (your test suite) → only DSL-declared rules.

If you declare the same rule kind in both places for the same service (e.g.
`tree` in TOML *and* `tree_structure(...)` in DSL), both rules run and both
can report.

---

## Full example

```python
# tests/test_architecture.py
import pytest
from pyarchrules import PyArchRules


@pytest.fixture(scope="session")
def arch():
    return PyArchRules()


def test_backend_no_cycles(arch):
    arch.for_service("backend").no_circular_imports()
    arch.validate()


@pytest.mark.parametrize("service", ["catalog", "orders", "auth"])
def test_no_cycles(arch, service):
    arch.for_service(service).no_circular_imports()
    arch.validate()
```

For folder-layout and import-direction rules expressed in TOML, see
[Configuration](configuration.md).

---

## Reporting

`PyArchRules` ships one reporter, `ConsoleViolationReporter`, with two formats:

```python
import sys
from pyarchrules import PyArchRules
from pyarchrules.core.reporting import ConsoleViolationReporter

rules = PyArchRules()
rules.validate(reporter=ConsoleViolationReporter(stream=sys.stdout, format="json"))
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `stream` | `TextIO` or `None` | `sys.stderr` | Output destination. |
| `format` | `"text"` or `"json"` | `"text"` | Human-readable lines or a JSON document. |

Implementing a custom reporter is one method:

```python
class CountingReporter:
    def __init__(self):
        self.errors = 0

    def report(self, result):
        self.errors += result.error_count
```

---

## Result objects

### `RuleEvalResult`

Frozen `@dataclass`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `violations` | `list[RuleViolation]` | All violations collected. |
| `is_valid` | `bool` | `True` when there are no violations. |
| `error_count` | `int` | Number of `"error"` severity violations. |
| `warning_count` | `int` | Number of `"warning"` severity violations. |

### `RuleViolation`

Frozen `@dataclass`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `rule_name` | `str` | Identifier of the rule that triggered (`tree_structure`, `internal_dependencies`, `no_circular_imports`, `service_isolation`). |
| `service_name` | `str` | Name of the affected service. |
| `severity` | `"error"` \| `"warning"` | Severity of the finding. |
| `message` | `str` | Human-readable description. |
| `file` | `str` or `None` | Offending source file (relative to project root) when applicable. |
| `line` | `int` or `None` | 1-based line number when applicable. |
| `details` | `dict` | Machine-readable extra context (cycle paths, conflicting rules, etc.). |

---

## Exceptions

All exceptions inherit from `pyarchrules.core.errors.PyArchError`. Catch the
base class to handle anything; catch a subclass for fine-grained control.

| Class | Raised when |
|-------|-------------|
| `PyArchError` | Base class — never raised directly. |
| `ConfigError` | Bad `pyproject.toml`: malformed table, unknown keys, invalid `dependencies` strings, missing service path, path outside project root. |
| `ValidationError` | `validate(raise_on_violation=True)` (default) when at least one error-severity violation is found. |
| `ServiceNotFoundError` | `for_service("name")` when no such service is declared. |

```python
from pyarchrules import PyArchRules
from pyarchrules.core.errors import ConfigError, ValidationError, ServiceNotFoundError

try:
    PyArchRules().for_service("backend").no_circular_imports().validate()
except ConfigError as e:
    print(f"Bad config: {e}")
except ServiceNotFoundError as e:
    print(f"Unknown service: {e}")
except ValidationError as e:
    print(f"Architecture violations: {e}")
```

---

## Package version

```python
import pyarchrules

print(pyarchrules.__version__)
```

`__version__` is derived from package metadata at import time, so it always
matches the installed version.
