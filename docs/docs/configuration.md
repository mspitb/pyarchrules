# Configuration Reference

PyArchRules is configured entirely through `pyproject.toml`.

---

## Project-level settings

```toml
[tool.pyarchrules]
project_name    = "myapp"
description     = "Architecture rules for this project"
root            = "."
strict          = true
validate_paths  = true
fail_on_warning = false
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `project_name` | string | *(required)* | Human-readable project name. |
| `description` | string | `""` | Optional description. |
| `root` | string | `"."` | Root directory, relative to `pyproject.toml`. |
| `strict` | bool | `true` | Exit with code `1` on any error violation. |
| `validate_paths` | bool | `true` | Validate that service paths exist on disk. |
| `fail_on_warning` | bool | `false` | Exit with code `1` on warnings too. |

---

## Service configuration

```toml
[tool.pyarchrules.services.backend]
path = "src/backend"
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `path` | string | *(required)* | Path to the service directory, relative to `root`. |

---

## Tree structure rules

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
| `tree_allow_files` | bool | `true` | When strict, regular files are still permitted. |

**Example — strict layout violation:**

```
services/auth/
├── api/
├── domain/
├── infra/
└── utils/      <- not listed in tree!
```

```
❌ [auth] tree_structure
   Unexpected directories in strict mode: ['utils']
```

---

## Internal dependency rules

```toml
[tool.pyarchrules.services.backend]
path         = "src/backend"
dependencies = [
    "api -> domain",
    "domain -> infra",
]
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `dependencies` | list[string] | `[]` | Allowed import relationships: `source -> target`. |

`"api -> domain"` means code in `api/` **may** import from `domain/`.
Only listed relationships are enforced. Duplicate rules are reported as errors.

**Clean Architecture example:**

```toml
dependencies = [
    "api         -> application",
    "application -> domain",
    "infra       -> domain",
]
```

```
api  --> application --> domain <-- infra
```

---

## Cross-service dependency rules

```toml
[tool.pyarchrules.services.auth]
path                         = "services/auth"
allowed_service_dependencies = ["shared", "common"]
```

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `allowed_service_dependencies` | list[string] | `[]` | Other services this service may depend on. |

---

## Full example

```toml
[tool.pyarchrules]
project_name    = "ecommerce"
strict          = true
validate_paths  = true
fail_on_warning = false

[tool.pyarchrules.services.catalog]
path         = "services/catalog"
tree         = ["api", "domain", "infra", "api/model"]
tree_strict  = true
dependencies = ["api -> domain", "domain -> infra"]

[tool.pyarchrules.services.orders]
path                         = "services/orders"
tree                         = ["api", "domain", "infra"]
tree_strict                  = true
dependencies                 = ["api -> domain", "domain -> infra"]
allowed_service_dependencies = ["catalog", "shared"]

[tool.pyarchrules.services.shared]
path = "services/shared"
tree = ["models", "utils"]
```