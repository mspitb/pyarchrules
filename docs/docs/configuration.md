# Configuration

All configuration lives in `pyproject.toml` under `[tool.pyarchrules]`.

---

## Project options

```toml
[tool.pyarchrules]
project_name     = "myapp"
description      = "Architecture rules for this project"
root             = "."
validate_paths   = true
isolate_services = true
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `project_name` | string | — | Human-readable project name. |
| `description` | string | `""` | Optional description. |
| `root` | string | `"."` | Root directory, relative to `pyproject.toml`. Service paths resolve from here. |
| `validate_paths` | bool | `true` | Raise an error at load time if a service path does not exist on disk. |
| `isolate_services` | bool | `false` | Enforce that services do not import each other unless `shared = true`. |

---

## Service options

```toml
[tool.pyarchrules.services.backend]
path   = "src/backend"
shared = false
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `path` | string | *(required)* | Path to the service directory, relative to `root`. |
| `shared` | bool | `false` | When `true`, other services may import this service (used with `isolate_services`). |

---

## Tree structure

```toml
[tool.pyarchrules.services.backend]
path             = "src/backend"
tree             = ["api", "domain", "infra", "api/model"]
tree_strict      = true
tree_allow_files = true
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `tree` | list[string] | `[]` | Paths that **must** exist inside the service. Supports nested paths (`"api/model"`). |
| `tree_strict` | bool | `false` | No directories other than those listed are allowed. |
| `tree_allow_files` | bool | `true` | When strict, regular files (`.py`, etc.) are still permitted at any level. |

**Example violation (strict mode):**

```
services/auth/
├── api/
├── domain/
├── infra/
└── utils/      ← not listed in tree!
```

```
❌ [auth] tree_structure
   Unexpected directories in strict mode: ['utils']
```

---

## Internal dependencies

```toml
[tool.pyarchrules.services.backend]
path         = "src/backend"
dependencies = [
    "api -> domain",
    "domain -> infra",
    "* -> utils",
]
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `dependencies` | list[string] | `[]` | Allowed import relationships: `source -> target`. Acts as a strict whitelist — anything not listed is forbidden. |

### Wildcard rules

| Syntax | Meaning |
|--------|---------|
| `"* -> utils"` | Any package may import from `utils`. |
| `"utils -> *"` | `utils` may import from any package. |

### Notes

- Same-package imports (e.g. `api/a.py` → `api/b.py`) are always allowed.
- Files at the service root (`main.py`, `__init__.py`) are excluded.
- Third-party libraries and `stdlib` are never flagged.

---

## Cross-service dependencies

```toml
[tool.pyarchrules.services.auth]
path                         = "services/auth"
allowed_service_dependencies = ["shared", "common"]
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `allowed_service_dependencies` | list[string] | `[]` | Other service names this service may import from. All other service imports are forbidden. |

---

## Service isolation

When `isolate_services = true` is set, every service is automatically checked for
cross-service imports. A service marked `shared = true` may be imported freely.

```toml
[tool.pyarchrules]
isolate_services = true

[tool.pyarchrules.services.api]
path = "services/api"

[tool.pyarchrules.services.billing]
path = "services/billing"

[tool.pyarchrules.services.utils]
path   = "services/utils"
shared = true
```

| Import | Result |
|--------|--------|
| `api` imports `billing` | ❌ isolation violation |
| `api` imports `utils` | ✅ allowed (`shared = true`) |
| `api` imports `requests` | ✅ ignored (third-party) |

---

## Full example

```toml
[tool.pyarchrules]
project_name     = "ecommerce"
validate_paths   = true
isolate_services = true

[tool.pyarchrules.services.catalog]
path         = "services/catalog"
tree         = ["api", "domain", "infra"]
tree_strict  = true
dependencies = ["api -> domain", "domain -> infra", "* -> utils"]

[tool.pyarchrules.services.orders]
path                         = "services/orders"
tree                         = ["api", "domain", "infra"]
tree_strict                  = true
dependencies                 = ["api -> domain", "domain -> infra", "* -> utils"]
allowed_service_dependencies = ["catalog", "shared"]

[tool.pyarchrules.services.shared]
path   = "services/shared"
tree   = ["models", "utils"]
shared = true
```