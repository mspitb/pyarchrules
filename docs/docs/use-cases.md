# Use Cases

Practical patterns for common architectural setups, using the v1 rule set:
`tree_structure`, `dependencies`, `no_circular_imports`, `service_isolation`.

---

## Monorepo with multiple services

**Project layout:**

```
my-platform/
├── pyproject.toml
└── services/
    ├── auth/
    │   ├── api/
    │   ├── domain/
    │   └── infra/
    ├── catalog/
    │   ├── api/
    │   ├── domain/
    │   └── infra/
    └── shared/
        ├── models/
        └── utils/
```

**Configuration:**

```toml
[tool.pyarchrules.services.auth]
path                = "services/auth"
tree                = ["api", "domain", "infra"]
tree_mode           = "strict"
dependencies        = ["api -> domain", "domain -> infra"]
no_circular_imports = true

[tool.pyarchrules.services.catalog]
path                = "services/catalog"
tree                = ["api", "domain", "infra"]
tree_mode           = "strict"
dependencies        = ["api -> domain", "domain -> infra"]
no_circular_imports = true

[tool.pyarchrules.services.shared]
path = "services/shared"
tree = ["models", "utils"]
```

What this enforces:

- `auth` and `catalog` must each contain **exactly** `api`, `domain`, and
  `infra` (`tree_mode = "strict"`).
- Internal imports follow `api → domain → infra`.
- No circular imports inside `auth` or `catalog`.

To also forbid `auth` and `catalog` from importing each other's internals,
add `isolate_services = true` at the project level and mark `shared` as a
shared library:

```toml
[tool.pyarchrules]
isolate_services = true

[tool.pyarchrules.services.shared]
path   = "services/shared"
shared = true
tree   = ["models", "utils"]

# ... auth and catalog as above
```

See [Configuration → Service isolation](configuration.md#service-isolation).

---

## Clean Architecture

**Typical layer structure:**

```
src/backend/
├── api/          <- Controllers, serialisers (outermost)
├── application/  <- Use cases, commands, queries
├── domain/       <- Entities, value objects (innermost)
└── infra/        <- DB adapters, external APIs
```

**Configuration:**

```toml
[tool.pyarchrules.services.backend]
path         = "src/backend"
tree         = ["api", "application", "domain", "infra"]
tree_mode    = "strict"
dependencies = [
    "api         -> application",
    "application -> domain",
    "infra       -> domain",
]
no_circular_imports = true
```

```
api --> application --> domain <-- infra
```

**Python DSL equivalent:**

```python
def test_clean_architecture():
    rules = PyArchRules()
    rules.for_service("backend") \
         .tree_structure(["api", "application", "domain", "infra"], mode="strict") \
         .dependencies([
             "api         -> application",
             "application -> domain",
             "infra       -> domain",
         ]) \
         .no_circular_imports()
    rules.validate()
```

DSL and TOML can be combined or used independently. See [Python DSL](dsl.md).

---

## Microservices with a shared library

```toml
[tool.pyarchrules.services.shared]
path = "shared"
tree = ["models", "utils"]

[tool.pyarchrules.services.orders]
path                = "orders"
tree                = ["api", "domain", "infra"]
tree_mode           = "strict"
dependencies        = ["api -> domain", "domain -> infra"]
no_circular_imports = true

[tool.pyarchrules.services.payments]
path                = "payments"
tree                = ["api", "domain", "infra"]
tree_mode           = "strict"
dependencies        = ["api -> domain", "domain -> infra"]
no_circular_imports = true
```

Each microservice gets its required folder layout, layered import direction,
and cycle detection. Add `isolate_services = true` and mark shared libraries
with `shared = true` to additionally forbid `orders` and `payments` from
importing each other.

---

## Catching circular imports across all services

```python
import pytest
from pyarchrules import PyArchRules


@pytest.fixture(scope="session")
def arch():
    return PyArchRules()


@pytest.mark.parametrize("service", ["orders", "payments", "catalog"])
def test_no_circular_imports(arch, service):
    arch.for_service(service).no_circular_imports()
    arch.validate()
```

---

## CI/CD integration

**GitHub Actions:**

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  architecture:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pyarchrules
      - name: Check architecture
        run: pyarchrules check
```

**GitLab CI:**

```yaml
architecture:
  image: python:3.12-slim
  script:
    - pip install pyarchrules
    - pyarchrules check
```

**Pre-commit:**

```yaml
repos:
  - repo: local
    hooks:
      - id: pyarchrules
        name: Architecture check
        entry: pyarchrules check
        language: system
        pass_filenames: false
```

