# CLI Reference

```bash
pyarchrules --help
```

---

## `init-project`

```bash
pyarchrules init-project [PROJECT_ROOT] [--force]
```

Writes a default `[tool.pyarchrules]` section to `pyproject.toml`.
Prompts for confirmation if a section already exists.

| Argument | Default | Description |
|----------|---------|-------------|
| `PROJECT_ROOT` | `.` | Path to the project root directory. |
| `--force`, `-f` | — | Re-initialise without confirmation. |

**Exit codes:** `0` success · `1` `pyproject.toml` not found

---

## `add-service`

```bash
pyarchrules add-service [NAME] [PATH]
```

Registers or updates a service in `[tool.pyarchrules.services]`.
Prompts interactively when arguments are omitted.

```bash
pyarchrules add-service backend src/backend
pyarchrules add-service          # interactive
```

**Exit codes:** `0` success · `1` invalid name or config not initialised

---

## `remove-service`

```bash
pyarchrules remove-service [NAME] [--force]
```

Removes a service. Prompts for confirmation unless `--force`.

```bash
pyarchrules remove-service backend --force
pyarchrules remove-service   # interactive list
```

**Exit codes:** `0` success or cancelled · `1` service not found

---

## `list-services`

```bash
pyarchrules list-services
```

Prints all configured services and their paths.

---

## `check`

```bash
pyarchrules check [PROJECT_ROOT] [--verbose | --quiet]
```

Validates the project against all rules defined in `pyproject.toml`.

| Option | Default | Description |
|--------|---------|-------------|
| `PROJECT_ROOT` | `.` | Path to the project root directory. |
| `--verbose` | on | Show per-service rule detail. |
| `--quiet` | — | Suppress per-service output. |

**Passing:**

```
🔍 Checking 2 service(s)...

📦 backend  src/backend
📦 shared   services/shared

✨ All checks passed!
   Checked 4 rule(s) across 2 service(s)
```

**Failing:**

```
❌  Validation failed!

Found 1 error(s):

❌ [backend] tree_structure
   Missing required paths: ['domain']
```

**Exit codes:**

| Code | Condition |
|------|-----------|
| `0` | All checks passed |
| `1` | One or more error violations found |
| `1` | Configuration could not be loaded |
