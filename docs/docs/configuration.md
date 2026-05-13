# Configuration

All configuration is declared in `pyproject.toml` under
`[tool.pyarchrules]`. There is one rule per section below. Enable only the
ones you need.

## A service in one block

The smallest valid config: register a directory as a service.

```toml
[tool.pyarchrules.services.backend]
path = "src/backend"
```

Options:

- `path` *(required)* — directory of the service, relative to
  `pyproject.toml`.
- `shared` *(optional, default `false`)* — used by
  [Service isolation](#service-isolation). Other services are allowed to
  import from a shared one.

You can declare as many services as you want. A project-level
`[tool.pyarchrules]` table is not required.

---

## Folder layout

Rule: **`tree_structure`**. Declares which folders a service must contain
and how strict the check is.

```toml
[tool.pyarchrules.services.backend]
path             = "src/backend"
tree             = ["api", "domain", "infra", "api/model"]
tree_mode        = "strict"
tree_allow_files = true
tree_ignore      = ["__snapshots__", "migrations_*"]
```

Options:

- `tree` — paths that **must** exist inside the service. Nested paths like
  `"api/model"` are supported. Duplicates raise `ConfigError`.
- `tree_mode` *(default `"exists"`)* — strictness level, see below.
- `tree_allow_files` *(default `true`)* — in `strict` / `exact` mode, loose
  files (`.py`, etc.) are always tolerated.
- `tree_ignore` — glob patterns of directory basenames to skip in
  `strict` / `exact` mode.

### Strictness levels

| Mode | Behaviour |
|------|-----------|
| `"exists"` *(default)* | Only checks that every declared path exists. Extra directories are ignored. |
| `"strict"` | Every level covered by `tree` (root plus all intermediate parents) must contain only the declared children. Leaf directories are not inspected. |
| `"exact"` | Same as `strict`, plus every leaf directory is walked recursively. Undeclared subdirectories inside a leaf are reported. |

### Example — `"strict"` mode

```toml
tree      = ["api", "domain"]
tree_mode = "strict"
```

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

### Example — `"exact"` mode

`"exact"` adds a recursive check inside leaf directories.

```toml
tree      = ["api", "api/model", "domain"]
tree_mode = "exact"
```

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

### `tree_ignore`

Exclude directories that are unrelated to architecture but exist inside the
service tree (snapshots, generated migrations, fixtures, …).

```toml
tree_ignore = ["__snapshots__", "migrations_*", "fixtures"]
```

Patterns are matched against the **basename** of each directory using
`fnmatch.fnmatchcase`:

| Pattern | Matches |
|---------|---------|
| `"migrations"` | exactly `migrations` |
| `"migrations_*"` | `migrations_001`, `migrations_alembic`, … |
| `"*.cache"` | `build.cache` (dotdirs like `.cache` are filtered earlier) |

`tree_ignore` applies only to the `tree_structure` rule. The import-based
rules (`dependencies`, `no_circular_imports`, `service_isolation`) already
skip virtualenvs, build artefacts, and tool caches automatically.

---

## Internal dependencies

Rule: **`dependencies`**. An allow-list of imports between folders inside a
service. Anything not listed is forbidden.

```toml
[tool.pyarchrules.services.backend]
path         = "src/backend"
dependencies = [
    "api -> domain",      # api may import from domain
    "domain -> infra",    # domain may import from infra
    "* -> utils",         # any folder may import from utils
]
```

With this config, inside `src/backend/`:

- ✅ `api/views.py` imports from `domain` — allowed by `api -> domain`.
- ✅ `domain/service.py` imports from `utils` — allowed by `* -> utils`.
- ❌ `domain/service.py` imports from `api` — **forbidden** (no rule).
- ❌ `api/views.py` imports from `infra` — **forbidden** (no rule).

### Syntax

The values on each side of `->` are **folder paths inside the service**.
Not service names, not Python module names. Use forward slashes on all
platforms.

| Form | Meaning |
|------|---------|
| `"api"` | The folder `<service>/api/`. |
| `"api/v1"` | A nested folder. |
| `"a -> b"` | Files under `a/` may import from `b/`. |
| `"* -> b"` | Any folder may import from `b/`. |
| `"a -> *"` | `a/` may import from any folder. |

Cross-service imports (`from other_service.api import X`) are handled by
[`service_isolation`](#service-isolation), not by `dependencies`.

### Notes

- Same-package imports (`api/a.py` → `api/b.py`) are always allowed.
- Files at the service root (`main.py`, `__init__.py`) are not subject to
  this rule. It applies only to files inside a named subfolder.
- Third-party libraries and `stdlib` are never flagged.
- The grammar is `source -> target` only. There is no `!->` (forbid) form.
- Files in folders not matched by any source are unrestricted. Declare a
  rule only for the folders whose imports you want to constrain.

### Overlapping rules

If two rules cover the same area and one is broader than the other, the
broader rule wins. PyArchRules reports this as a **warning**, not a config
error:

```toml
dependencies = [
    "api    -> domain",   # broader
    "api/v1 -> domain",   # already covered by the first rule
]
```

Delete the narrower rule, or replace the broader one with the explicit set
you intended. Wildcard (`*`) rules never trigger this warning.

---

## Circular imports

Rule: **`no_circular_imports`**. Detects import cycles inside a service.

```toml
[tool.pyarchrules.services.backend]
path                = "src/backend"
no_circular_imports = true
```

That's the whole interface — one boolean per service. The same check is
available from the [Python DSL](dsl.md) via `.no_circular_imports()`.

---

## Service isolation

Rule: **`service_isolation`**. Project-wide. Forbids one service from
importing the internals of another. Useful in monorepos.

```toml
[tool.pyarchrules]
isolate_services = true

[tool.pyarchrules.services.shared]
path   = "services/shared"
shared = true                     # exempt: anyone can import from it

[tool.pyarchrules.services.orders]
path = "services/orders"

[tool.pyarchrules.services.catalog]
path = "services/catalog"
```

What this enforces:

- `orders` may not `from catalog.<...>`, and vice versa.
- Either may `from shared.<...>` because `shared` is flagged
  `shared = true`.
- Intra-service imports (e.g. `from orders.domain import X` from inside
  `orders/`) are always allowed.

### How services are matched

The top-level package of every absolute import is matched against the
**last directory component** of each service's `path`:

| `path` | Implied import name |
|--------|---------------------|
| `services/catalog` | `catalog` |
| `src/backend` | `backend` |
| `apps/orders-svc` | `orders-svc` |

This is the convention used by most monorepo Python projects.

### Not available via the DSL

`service_isolation` is project-wide, and the DSL is per-service, so this
rule is **TOML-only**. The [Python DSL](dsl.md) covers `tree_structure`,
`dependencies`, and `no_circular_imports`.

---

## Full example

```toml
[tool.pyarchrules]
isolate_services = true

[tool.pyarchrules.services.shared]
path   = "services/shared"
shared = true

[tool.pyarchrules.services.catalog]
path                = "services/catalog"
tree                = ["api", "domain", "infra"]
tree_mode           = "strict"
dependencies        = ["api -> domain", "domain -> infra", "* -> utils"]
no_circular_imports = true

[tool.pyarchrules.services.orders]
path                = "services/orders"
tree                = ["api", "domain", "infra"]
tree_mode           = "strict"
dependencies        = ["api -> domain", "domain -> infra", "* -> utils"]
```

---

## Deferred

The following keys are intentionally **not** part of v1 and will be
reintroduced in a later release: `allowed_service_dependencies`,
`allowed_external_libs`, `forbidden_external_libs`, and per-rule
`severity`.

