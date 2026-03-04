# Configuration

All configuration lives in `pyproject.toml` under `[tool.pyarchrules]`.

---

## Project options

```toml
[tool.pyarchrules]
root             = "."
validate_paths   = true
isolate_services = true
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
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
tree_mode        = "strict"
tree_allow_files = true
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `tree` | list[string] | `[]` | Paths that **must** exist inside the service. Supports nested paths (`"api/model"`). |
| `tree_mode` | string | `"exists"` | Controls how strictly the tree is validated. See modes below. |
| `tree_allow_files` | bool | `true` | In `strict` / `exact` mode, loose files (`.py`, etc.) are always tolerated. |

### `tree_mode` values

| Value | Behaviour |
|-------|-----------|
| `"exists"` | *(default)* Only checks that every declared path exists. Extra directories anywhere are ignored. |
| `"strict"` | Every level covered by `tree` (root + all intermediate parents up to the deepest declared path) must contain only the declared children. Leaf directories are not inspected internally. |
| `"exact"` | Same as `strict`, plus every leaf directory is walked recursively. Any subdirectory inside a leaf that is not declared in `tree` is reported. Full one-to-one match of the entire tree. |

**Example — `"strict"` mode**:

Config:
```toml
tree      = ["api", "domain"]
tree_mode = "strict"
```

Disk:
```
services/auth/
├── api/       ← declared ✓
├── domain/    ← declared ✓
├── infra/     ← not in tree!
└── utils/     ← not in tree!
```

Result:
```
⚠️  [auth] tree_structure
   Extra items in '.' (tree_mode=strict): ['infra', 'utils']
```

**Example — `"exact"` mode** (same as strict + checks inside leaf directories):

Config:
```toml
tree      = ["api", "api/model", "domain"]
tree_mode = "exact"
```

Disk:
```
services/auth/
├── api/           ← non-leaf (has child api/model in tree)
│   ├── model/     ← declared ✓
│   └── internal/  ← not in tree! caught by strict part
└── domain/        ← leaf (no children declared in tree)
    └── core/      ← not in tree! caught by exact (leaf walk)
```

Result:
```
⚠️  [auth] tree_structure
   Extra items in 'api' (tree_mode=exact): ['internal']
   Undeclared directories inside leaf dirs (tree_mode=exact): ['domain/core']
```

> **Note:** `"strict"` checks all levels explicitly covered by `tree`. `"exact"` additionally walks inside every leaf directory for a full one-to-one match.

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
root             = "."
validate_paths   = true
isolate_services = true

[tool.pyarchrules.services.catalog]
path         = "services/catalog"
tree         = ["api", "domain", "infra"]
tree_mode    = "strict"
dependencies = ["api -> domain", "domain -> infra", "* -> utils"]

[tool.pyarchrules.services.orders]
path                         = "services/orders"
tree                         = ["api", "domain", "infra"]
tree_mode                    = "strict"
dependencies                 = ["api -> domain", "domain -> infra", "* -> utils"]
allowed_service_dependencies = ["catalog", "shared"]

[tool.pyarchrules.services.shared]
path   = "services/shared"
tree   = ["models", "utils"]
shared = true
```