<p align="center">
  <img src="https://gist.githubusercontent.com/mspitb/862bc8c4b0e176e98f06e624761519da/raw/f4237236769bd2739132790f6c6f1157e3be5131/pyarchrules_logo.svg" alt="PyArchRules Logo" width="500">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python 3.12+"></a>
  <img src="https://img.shields.io/badge/status-alpha-orange.svg" alt="Status: Alpha">
</p>

# PyArchRules

**PyArchRules** is an architecture validation library for Python projects.
It lets you encode your structural conventions — folder layout, module dependencies,
service boundaries — as rules, and enforce them automatically in CI or your test suite.

## Why PyArchRules?

As a project grows, architectural conventions drift. A new developer adds a file in
the wrong place, a module starts importing from a layer it should not, a service loses
its expected structure. By the time anyone notices, the damage is done.

PyArchRules gives you a safety net:

- **Express your architecture as code** — rules live next to your source, versioned and reviewed.
- **Fail fast** — violations surface immediately in CI.
- **Zero friction** — driven by `pyproject.toml`, no extra config files needed.

## Features

| Feature | Description |
|---------|-------------|
| 🏗️ Structure validation | Enforce exact directory tree requirements per service |
| 🔗 Dependency rules | Control which internal modules may import from which |
| 🛡️ Service boundaries | Restrict cross-service imports in monorepos |
| 🎯 TOML config | Declare rules directly in `pyproject.toml` |
| 🐍 Python DSL | Write rules in Python for maximum flexibility |
| 🚀 CLI | Run `pyarchrules check` from the terminal or CI |

## Quick Example

```toml
[tool.pyarchrules]
project_name = "myapp"

[tool.pyarchrules.services.backend]
path = "src/backend"
tree = ["api", "domain", "infra"]
tree_strict = true
dependencies = ["api -> domain", "domain -> infra"]
```

```bash
pyarchrules check
# ✨ All checks passed!
#    Checked 2 rule(s) across 1 service(s)
```

## Pages

- [Getting Started](getting-started.md) — Install and run your first check in five minutes.
- [Configuration](configuration.md) — Full reference for every `[tool.pyarchrules]` option.
- [CLI Reference](cli.md) — All commands, flags, and exit codes.
- [Python DSL](dsl.md) — Write architecture rules in pure Python.
- [Use Cases](use-cases.md) — Patterns for monorepos, Clean Architecture, and microservices.

---

> ⚠️ **Alpha** — PyArchRules is `0.0.1a2`. The public API may change before 1.0.
