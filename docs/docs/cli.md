# CLI Reference

```bash
pyarchrules --help
```

Commands: `init-project`, `add-service`, `remove-service`, `list-services`,
`show-config`, `check`.

---

## Exit codes

The same matrix applies to every command that loads or validates configuration:

| Code | Meaning |
|------|---------|
| `0` | Success (validation passed, only warnings without `-W`, or interactive cancel) |
| `1` | Validation failed — at least one error-severity violation, or warnings when `-W` was passed |
| `2` | Configuration / loading error — `pyproject.toml` missing, malformed `[tool.pyarchrules]` table, unknown keys, invalid `dependencies` strings, unknown `--service` filter, unsupported `--format` value |

CI scripts can rely on these codes:

```bash
pyarchrules check
case $? in
  0) echo "OK" ;;
  1) echo "Architecture violations" ;;
  2) echo "Bad config" ;;
esac
```

---

## `init-project`

```bash
pyarchrules init-project [PROJECT_ROOT] [--force]
```

Writes a default `[tool.pyarchrules]` table to `pyproject.toml` with a fully
commented template covering every v1 key. Prompts for confirmation if a section
already exists.

| Argument / option | Default | Description |
|-------------------|---------|-------------|
| `PROJECT_ROOT` | `.` | Path to the project root directory. |
| `--force`, `-f` | — | Re-initialise without confirmation. |

---

## `add-service`

```bash
pyarchrules add-service [NAME] [PATH]
```

Registers (or updates) a service under `[tool.pyarchrules.services.<name>]`.
Prompts interactively when arguments are omitted.

```bash
pyarchrules add-service backend src/backend
pyarchrules add-service          # interactive
```

`NAME` must be a valid Python identifier.

---

## `remove-service`

```bash
pyarchrules remove-service [NAME] [--force]
```

Removes a service. Prompts for confirmation unless `--force` is passed.
Without `NAME`, lists configured services and asks interactively.

---

## `list-services`

```bash
pyarchrules list-services
```

Prints all configured services and their paths.

---

## `show-config`

```bash
pyarchrules show-config [PROJECT_ROOT]
```

Dumps the **resolved** configuration as a JSON document on stdout: every
service with its declared keys and the list of rules that will be executed.
Useful for debugging which services and rules will actually run.

| Argument | Default | Description |
|----------|---------|-------------|
| `PROJECT_ROOT` | `.` | Path to the project root directory. |

```jsonc
{
  "project_root": "/path/to/project",
  "services": {
    "backend": {
      "dependencies": ["api -> domain"],
      "name": "backend",
      "no_circular_imports": true,
      "path": "src/backend",
      "project_root": "/path/to/project",
      "rules": ["tree_structure", "internal_dependencies", "no_circular_imports"],
      "tree": ["api", "domain", "infra"],
      "tree_allow_files": true,
      "tree_mode": "strict"
    }
  }
}
```

---

## `check`

```bash
pyarchrules check [PROJECT_ROOT] [OPTIONS]
```

Validates the project against all rules defined in `pyproject.toml`.

| Argument / option | Short | Default | Description |
|-------------------|-------|---------|-------------|
| `PROJECT_ROOT` | — | `.` | Path to the project root. Ignored when `--config` is given. |
| `--config PATH` | `-c` | — | Path to a non-default `pyproject.toml`. Accepts either the file or its parent directory. |
| `--service NAME` | `-s` | — | Only report violations from this service. Pass repeatedly for multiple services. Unknown name → exit `2`. |
| `--rule NAME` | `-r` | — | Only report violations from this rule (e.g. `tree_structure`, `internal_dependencies`, `no_circular_imports`, `service_isolation`). Pass repeatedly for multiple rules. |
| `--warnings-as-errors` | `-W` | off | Treat warning-severity violations as errors. Without this flag, warnings never affect the exit code. |
| `--format FMT` | `-f` | `text` | Output format. `text` (default) prints the human-readable summary; `json` writes a single JSON document to stdout suitable for CI integrations. |
| `--verbose` / `--quiet` | — | `--verbose` | In `text` mode, toggles per-service rule listing before the validation summary. |

**Passing (`text`):**

```
🔍 Checking 2 service(s)...

📦 backend
   Path: src/backend
   Rules: tree_structure, internal_dependencies, no_circular_imports

✨ All checks passed!
   Checked 3 rule(s) across 2 service(s)
```

**Failing (`text`):**

```
❌  Validation failed!

Found 1 error(s) and 0 warning(s):

❌ [backend] tree_structure
   Missing required paths: ['domain']
```

**JSON output (`--format json`)** — written to stdout, parseable directly:

```json
{
  "summary": {
    "errors": 1,
    "is_valid": false,
    "warnings": 0
  },
  "violations": [
    {
      "details": {
        "from_module": "domain",
        "import_statement": "api.views",
        "imported": "api/views"
      },
      "file": "domain/models.py",
      "line": null,
      "message": "Forbidden import in domain/models.py: 'api.views'",
      "rule_name": "internal_dependencies",
      "service_name": "backend",
      "severity": "error"
    }
  ]
}
```

The JSON schema is stable: `summary` (`errors`, `warnings`, `is_valid`) and a
`violations` array of `{rule_name, service_name, severity, message, file,
line, details}` objects. `file` and `line` are `null` when not applicable.

### Common workflows

**Scope a run to one service in a monorepo:**

```bash
pyarchrules check --service backend --service shared
```

**Check only one rule across the whole project:**

```bash
pyarchrules check --rule no_circular_imports
```

**Use a non-default config (e.g. CI override):**

```bash
pyarchrules check --config configs/strict.pyproject.toml
```

**Pipe JSON to `jq` in a pre-commit hook:**

```bash
pyarchrules check --format json --quiet | jq '.summary'
```
