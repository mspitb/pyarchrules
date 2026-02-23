# Use Cases

Practical patterns for the most common architectural challenges.

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
[tool.pyarchrules]
project_name = "my-platform"
isolate_services = true

[tool.pyarchrules.services.auth]
path                         = "services/auth"
tree                         = ["api", "domain", "infra"]
tree_strict                  = true
dependencies                 = ["api -> domain", "domain -> infra"]
allowed_service_dependencies = ["shared"]

[tool.pyarchrules.services.catalog]
path                         = "services/catalog"
tree                         = ["api", "domain", "infra"]
tree_strict                  = true
dependencies                 = ["api -> domain", "domain -> infra"]
allowed_service_dependencies = ["shared"]

[tool.pyarchrules.services.shared]
path = "services/shared"
tree = ["models", "utils"]
```

What this enforces:

- `auth` and `catalog` must each contain exactly `api`, `domain`, and `infra`.
- Internal imports follow `api -> domain -> infra`.
- `auth` and `catalog` may import from `shared`, but not from each other.

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
tree_strict  = true
dependencies = [
    "api         -> application",
    "application -> domain",
    "infra       -> domain",
]
```

```
api --> application --> domain <-- infra
```

**Python DSL equivalent:**

```python
def test_clean_architecture():
    rules = PyArchRules()
    rules.for_service("backend").must_contain_folders(
        ["api", "application", "domain", "infra"],
        allow_extra=False,
    )
    rules.validate()
```

---

## Microservices with a shared library

```toml
[tool.pyarchrules]
project_name = "platform"
isolate_services = true

[tool.pyarchrules.services.shared]
path = "shared"
tree = ["models", "utils"]

[tool.pyarchrules.services.orders]
path                         = "orders"
tree                         = ["api", "domain", "infra"]
tree_strict                  = true
dependencies                 = ["api -> domain", "domain -> infra"]
allowed_service_dependencies = ["shared"]

[tool.pyarchrules.services.payments]
path                         = "payments"
tree                         = ["api", "domain", "infra"]
tree_strict                  = true
dependencies                 = ["api -> domain", "domain -> infra"]
allowed_service_dependencies = ["shared"]
```

---

## Enforcing consistent structure with parameterised tests

```python
import pytest
from pyarchrules import PyArchRules

STANDARD_LAYOUT = ["api", "domain", "infra"]


@pytest.fixture(scope="session")
def arch():
    return PyArchRules()


@pytest.mark.parametrize("service", ["orders", "payments", "catalog"])
def test_standard_layout(arch, service):
    arch.for_service(service).must_contain_folders(
        STANDARD_LAYOUT, allow_extra=False
    )
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
