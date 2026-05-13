"""DSL parity tests for ServiceRuleSet — `tree_structure`, `dependencies`, `no_circular_imports`.

Each test asserts that violations produced via the DSL are identical to those
produced when the same configuration is declared in ``pyproject.toml``.
"""

from __future__ import annotations

import pytest

from pyarchrules.core.errors import ConfigError
from pyarchrules.pyarchrules import PyArchRules


# ----------------------------------------------------------------------
# tree_structure
# ----------------------------------------------------------------------


class TestTreeStructureDSL:
    def test_passes_when_layout_matches(self, make_project):
        project = make_project(services={"api": "src/api"})
        project.mkdir("src/api/domain")
        project.mkdir("src/api/application")

        rules = PyArchRules(project.root)
        rules.for_service("api").tree_structure(["domain", "application"])
        result = rules.validate(raise_on_violation=False, verbose=False)

        assert result.is_valid

    def test_reports_missing_path(self, make_project):
        project = make_project(services={"api": "src/api"})
        project.mkdir("src/api/domain")  # "application" is missing

        rules = PyArchRules(project.root)
        rules.for_service("api").tree_structure(["domain", "application"])
        result = rules.validate(raise_on_violation=False, verbose=False)

        assert not result.is_valid
        assert any("Missing required paths" in v.message for v in result.violations)
        assert all(v.rule_name == "tree_structure" for v in result.violations)

    def test_strict_mode_reports_extras(self, make_project):
        project = make_project(services={"api": "src/api"})
        project.mkdir("src/api/domain")
        project.mkdir("src/api/extra_dir")

        rules = PyArchRules(project.root)
        rules.for_service("api").tree_structure(["domain"], mode="strict")
        result = rules.validate(raise_on_violation=False, verbose=False)

        warnings = [v for v in result.violations if v.severity == "warning"]
        assert any("extra_dir" in v.message for v in warnings)

    def test_invalid_mode_raises_config_error(self, make_project):
        project = make_project(services={"api": "src/api"})
        rules = PyArchRules(project.root)
        with pytest.raises(ConfigError, match="invalid tree_mode"):
            rules.for_service("api").tree_structure(["domain"], mode="bogus")

    def test_dsl_matches_toml(self, make_project):
        """Identical configuration via TOML and DSL must yield identical violations."""
        # TOML path
        project_toml = make_project(
            name="via_toml",
            services={"api": "src/api"},
            extra_config={
                "services": {
                    "api": {"path": "src/api", "tree": ["domain", "application"]}
                }
            },
        )
        project_toml.mkdir("src/api/domain")  # "application" missing → violation
        toml_result = PyArchRules(project_toml.root).check_linter()

        # DSL path — fresh project, same shape, no tree key in TOML
        project_dsl = make_project(name="via_dsl", services={"api": "src/api"})
        project_dsl.mkdir("src/api/domain")
        dsl_rules = PyArchRules(project_dsl.root)
        dsl_rules.for_service("api").tree_structure(["domain", "application"])
        dsl_result = dsl_rules.validate(raise_on_violation=False, verbose=False)

        assert [
            (v.rule_name, v.severity, v.message, v.details)
            for v in toml_result.violations
        ] == [
            (v.rule_name, v.severity, v.message, v.details)
            for v in dsl_result.violations
        ]


# ----------------------------------------------------------------------
# dependencies
# ----------------------------------------------------------------------


class TestDependenciesDSL:
    def _scaffold(self, project):
        project.mkdir("src/api/api")
        project.mkdir("src/api/domain")
        project.touch("src/api/api/__init__.py")
        project.touch("src/api/domain/__init__.py")

    def test_allowed_import_passes(self, make_project):
        project = make_project(services={"api": "src/api"})
        self._scaffold(project)
        project.touch("src/api/api/controller.py", "from domain import models\n")

        rules = PyArchRules(project.root)
        rules.for_service("api").dependencies(["api -> domain"])
        result = rules.validate(raise_on_violation=False, verbose=False)
        assert result.is_valid

    def test_forbidden_import_is_reported(self, make_project):
        project = make_project(services={"api": "src/api"})
        self._scaffold(project)
        project.touch("src/api/domain/service.py", "from api import controller\n")

        rules = PyArchRules(project.root)
        rules.for_service("api").dependencies(["api -> domain"])
        result = rules.validate(raise_on_violation=False, verbose=False)

        forbidden = [v for v in result.violations if v.rule_name == "internal_dependencies"]
        assert forbidden, "expected an internal_dependencies violation"
        assert "Forbidden import" in forbidden[0].message

    def test_invalid_grammar_raises_config_error(self, make_project):
        project = make_project(services={"api": "src/api"})
        rules = PyArchRules(project.root)
        with pytest.raises(ConfigError, match="missing '->'"):
            rules.for_service("api").dependencies(["api domain"])

    def test_star_to_star_raises_config_error(self, make_project):
        project = make_project(services={"api": "src/api"})
        rules = PyArchRules(project.root)
        with pytest.raises(ConfigError, match="'\\* -> \\*'"):
            rules.for_service("api").dependencies(["* -> *"])

    def test_overlapping_rules_emit_warning_not_config_error(self, make_project):
        """Overlap is a warning at validate() time, not a load-time error."""
        project = make_project(services={"api": "src/api"})
        project.mkdir("src/api/api")
        project.mkdir("src/api/api/v1")
        project.mkdir("src/api/domain")

        rules = PyArchRules(project.root)
        # No ConfigError here — overlap is no longer a syntax-level failure.
        rules.for_service("api").dependencies(
            ["api -> domain", "api/v1 -> domain"]
        )

        result = rules.validate(raise_on_violation=False, verbose=False)
        warnings = [v for v in result.violations if v.severity == "warning"]
        assert any("Overlapping dependency rules" in v.message for v in warnings)


# ----------------------------------------------------------------------
# Chaining + TOML/DSL coexistence
# ----------------------------------------------------------------------


class TestChainingAndCoexistence:
    def test_chaining_all_three_rules(self, make_project):
        project = make_project(services={"api": "src/api"})
        project.mkdir("src/api/domain")
        project.touch("src/api/domain/__init__.py", "")

        rules = PyArchRules(project.root)
        rs = (
            rules.for_service("api")
            .tree_structure(["domain"])
            .dependencies(["domain -> domain"])  # trivial but legal
            .no_circular_imports()
        )
        # All three rules attached.
        assert len(rs._rules) == 3  # noqa: SLF001 — internal check is fine in tests
        result = rules.validate(raise_on_violation=False, verbose=False)
        assert result.is_valid

    def test_toml_and_dsl_both_run_for_same_rule_kind(self, make_project):
        """Defining `tree` in TOML AND `tree_structure` in DSL → both registries run."""
        project = make_project(
            services={"api": "src/api"},
            extra_config={
                "services": {
                    "api": {"path": "src/api", "tree": ["only_in_toml"]}
                }
            },
        )
        project.mkdir("src/api/domain")  # neither "only_in_toml" nor extra DSL paths exist

        rules = PyArchRules(project.root)
        rules.for_service("api").tree_structure(["only_in_dsl"])

        linter_result = rules.check_linter()
        dsl_result = rules.validate(raise_on_violation=False, verbose=False)

        assert any("only_in_toml" in v.message for v in linter_result.violations)
        assert any("only_in_dsl" in v.message for v in dsl_result.violations)


# ----------------------------------------------------------------------
# from_services / from_spec (config-less)
# ----------------------------------------------------------------------


class TestConfigLessEntryPoints:
    def test_from_services_without_pyproject(self, tmp_test_dir):
        root = tmp_test_dir / "no_toml_project"
        root.mkdir()
        (root / "src" / "api" / "domain").mkdir(parents=True)
        # NOTE: deliberately *no* pyproject.toml here.

        rules = PyArchRules.from_services({"api": "src/api"}, project_root=root)

        assert rules.project_root == root.resolve()
        assert "api" in rules.services
        rules.for_service("api").tree_structure(["domain"])
        assert rules.validate(raise_on_violation=False, verbose=False).is_valid

    def test_from_services_rejects_missing_service_dir(self, tmp_test_dir):
        root = tmp_test_dir / "missing_svc"
        root.mkdir()
        with pytest.raises(ConfigError, match="doesn't exist"):
            PyArchRules.from_services({"api": "src/api"}, project_root=root)

    def test_from_services_rejects_path_outside_root(self, tmp_test_dir):
        root = tmp_test_dir / "outside_root"
        root.mkdir()
        with pytest.raises(ConfigError, match="outside project root"):
            PyArchRules.from_services({"api": "../elsewhere"}, project_root=root)

    def test_from_services_rejects_bad_project_root(self, tmp_test_dir):
        with pytest.raises(ConfigError, match="project_root does not exist"):
            PyArchRules.from_services(
                {"api": "src/api"}, project_root=tmp_test_dir / "no_such_dir"
            )

    def test_from_services_unknown_service_raises(self, tmp_test_dir):
        from pyarchrules.core.errors import ServiceNotFoundError

        root = tmp_test_dir / "fs_unknown_svc"
        root.mkdir()
        (root / "src" / "api").mkdir(parents=True)
        rules = PyArchRules.from_services({"api": "src/api"}, project_root=root)
        with pytest.raises(ServiceNotFoundError):
            rules.for_service("ghost")

