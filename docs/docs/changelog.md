# Changelog

All notable changes are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0b1] — 2026-03-04

> 🚧 **Beta** — public API is stabilising, minor breaking changes may still occur.

### Added

- `tree_mode` — replaces `tree_strict` / `tree_recursive` with a single enum: `"exists"` (default), `"strict"`, `"exact"`
- `tree_mode = "strict"` — validates structure one-to-one at every level covered by `tree`, from root down to the deepest declared path; leaf directories are not inspected internally
- `tree_mode = "exact"` — same as `strict` plus recursively checks inside every leaf directory; full one-to-one match of the entire tree
- `tree_allow_files` — still supported alongside `tree_mode`; loose files are always tolerated in strict/exact modes by default
- Invalid `tree_mode` value raises a clear `PyArchError` with the list of valid options
- Documentation updated: `configuration.md`, `use-cases.md`, `getting-started.md` now use `tree_mode` throughout

### Changed

- `tree_strict` and `tree_recursive` boolean flags replaced by `tree_mode` (breaking change)
- `init-project` no longer generates deprecated `project_name` and `description` fields
- `project_name` and `description` removed from known project keys — configs that still contain them will now raise an "unknown key" error
- `no_args_is_help = true` on the CLI app — invoking `pyarchrules` with no arguments now shows the same output as `--help`

### Fixed

- `tree_strict` previously did not check the service root level, so undeclared siblings at the top level were silently ignored — now fixed in `"strict"` and `"exact"` modes

---

## [0.1.0b0] — 2026-02-25

> 🚧 **Beta** — first public beta release.

### Added

- New DSL rules: `allowed_external_libs`, `forbidden_external_libs`, `no_test_files_in`, `no_files_in_folder`, `max_depth`, `files_must_match_pattern`, `files_must_be_snake_case`, `classes_must_match_pattern`, `no_relative_imports_in`, `no_circular_imports`, `layer_must_not_import`, `no_private_imports`, `no_wildcard_imports`
- `ServiceIsolationRule` — enforces `isolate_services` at the project level; services marked `shared = true` are exempt
- `AllowedServiceDependenciesRule` — validates `allowed_service_dependencies` per service
- `LinterRegistry` and `BaseRegistry` for rule registration
- MkDocs documentation site deployed to [mspitb.github.io/pyarchrules](https://mspitb.github.io/pyarchrules/)
- GitHub Actions workflow for automatic docs deployment on push to `main`
- Unknown keys in `[tool.pyarchrules]` and per-service config now raise a descriptive `PyArchError`

### Changed

- `pyproject.toml` dependencies relaxed from exact pins (`==`) to minimum bounds (`>=`) for better compatibility with user environments
- Removed `zensical` from dev dependencies

### Fixed

- `ConsoleViolationReporter` log format now includes a trailing newline to prevent messages from appearing on the same line

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