# CLI Reference

```bash
pyarchrules --help
```

## Commands

| Command | Description |
|---------|-------------|
| `init-project` | Initialise `[tool.pyarchrules]` in `pyproject.toml` |
| `add-service` | Register a new service |
| `remove-service` | Remove a service |
| `list-services` | Show all configured services |
| `check` | Validate architecture against all rules |

---

## `init-project`

```bash
pyarchrules init-project [PROJECT_ROOT] [--force]
```

Writes a default `[tool.pyarchrules]` section to `pyproject.toml`.

| Argument / Option | Default | Description |
|-------------------|---------|-------------|
| `PROJECT_ROOT` | `.` | Path to the project root. |
| `--force`, `-f` | false | Re-initialise without confirmation. |

**Output:**

```
✨ Successfully initialized!
📝 /home/user/myapp/pyproject.toml

Configuration:
  • root = '.'
  • strict = true
  • validate_paths = true
  • fail_on_warning = false
```

Exit codes: `0` success · `1` `pyproject.toml` not found

---

## `add-service`

```bash
pyarchrules add-service [NAME] [PATH]
```

Adds or updates a service. Prompts interactively if arguments are omitted.

```bash
pyarchrules add-service backend src/backend
pyarchrules add-service          # interactive prompts
```

**Output:**

```
➕ Added service 'backend'
   Path: src/backend
```

Exit codes: `0` success · `1` invalid name or config not found

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

Exit codes: `0` success or cancelled · `1` service not found

---

## `list-services`

```bash
pyarchrules list-services
```

**Output:**

```
📦 Configured services (3):

  • backend
    src/backend
  • auth
    services/auth
  • shared
    services/shared
```

---

## `check`

```bash
pyarchrules check [PROJECT_ROOT] [--strict/--no-strict] [--verbose/--quiet]
```

Validates architecture against all rules in `pyproject.toml`.

| Option | Default | Description |
|--------|---------|-------------|
| `--strict` / `--no-strict` | from config | Override strict mode. |
| `--verbose` / `--quiet` | `--verbose` | Show per-service rule detail. |

**Passing:**

```
🔍 Checking 2 service(s)...

📦 backend
   Path: src/backend
   Rules: tree_structure, internal_dependencies

✨ All checks passed!
   Checked 2 rule(s) across 2 service(s)
```

**Failing:**

```
❌  Validation failed!

Found 1 error(s) and 0 warning(s):

❌ [backend] tree_structure
   Missing required paths: ['domain']
```

**Exit codes:**

| Code | Condition |
|------|-----------|
| `0` | All checks passed |
| `0` | Violations present but `strict = false` |
| `1` | Errors present and `strict = true` |
| `1` | Warnings present and `fail_on_warning = true` |
| `1` | Config could not be loaded |
