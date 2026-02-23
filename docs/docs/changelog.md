# Changelog

All notable changes are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.0.1a2] — 2026-02-19

### Added

- `pyarchrules check` — validates architecture from the CLI
- `pyarchrules init-project` — initialises `pyproject.toml` config
- `pyarchrules add-service` / `remove-service` / `list-services` commands
- `TreeRule` — validates directory tree structure
- `DependenciesRule` — validates internal module import direction
- `AllowedServiceDependenciesRule` — validates cross-service imports
- `MustContainFoldersRule` DSL rule with `allow_extra` parameter
- `PyArchRules` Python API with `for_service()` / `validate()` interface
- `PyArchConfig` for reading/writing `pyproject.toml` via `tomlkit`
- Pydantic-backed `ProjectSpec` and `ServiceSpec` models
- `ConsoleViolationReporter` for human-readable output
- `RuleEvalResult` with `is_valid`, `error_count`, `warning_count`

> ⚠️ **Alpha** — API may change before 1.0.

---

## [0.0.1a1] — 2026-01-01

Initial private release.