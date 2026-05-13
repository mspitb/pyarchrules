"""Tests for DependenciesRule."""

import pytest

from pyarchrules.core.errors import ConfigError
from pyarchrules.core.rules.linter.dependencies_rule import DependenciesRule


class TestDependenciesRule:
    def test_no_dependencies_passes(self, make_service_spec):
        assert len(DependenciesRule(make_service_spec(dependencies=[])).validate()) == 0

    def test_valid_dependency_syntax(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        spec = make_service_spec(dependencies=["api -> domain", "domain -> infra"])
        violations = DependenciesRule(spec).validate()

        syntax_errors = [v for v in violations if "Invalid dependency rule" in v.message]
        assert len(syntax_errors) == 0

    # ------------------------------------------------------------------
    # Parse-time errors are now ConfigError (raised by parse_rules /
    # SpecLoader at load time), not runtime RuleViolation entries.
    # ------------------------------------------------------------------

    def test_invalid_arrow_direction_raises_config_error(self):
        with pytest.raises(ConfigError, match="invalid arrow"):
            DependenciesRule.parse_rules(["api <- domain"])

    def test_missing_arrow_raises_config_error(self):
        with pytest.raises(ConfigError, match="missing '->'"):
            DependenciesRule.parse_rules(["api domain"])

    def test_empty_source_or_target_raises_config_error(self):
        with pytest.raises(ConfigError, match="empty source or target"):
            DependenciesRule.parse_rules(["-> domain"])
        with pytest.raises(ConfigError, match="empty source or target"):
            DependenciesRule.parse_rules(["api ->"])

    def test_overlapping_rules_emit_warning(self, make_service_spec, tmp_test_dir, monkeypatch):
        """Overlap is a *warning*, not a config error — broader subsumes narrower."""
        monkeypatch.chdir(tmp_test_dir)
        (tmp_test_dir / "api").mkdir()
        (tmp_test_dir / "domain").mkdir()

        # parse_rules itself does NOT raise on overlap (syntax-only now).
        parsed = DependenciesRule.parse_rules(
            ["api -> domain", "api/controllers -> domain"]
        )
        assert len(parsed) == 2

        # Overlap shows up at validate() time as a warning.
        spec = make_service_spec(dependencies=["api -> domain", "api/controllers -> domain"])
        violations = DependenciesRule(spec).validate()
        warnings = [v for v in violations if v.severity == "warning"]
        assert any("Overlapping dependency rules" in v.message for v in warnings)
        assert any("api -> domain" in v.message for v in warnings)

    def test_same_source_different_targets_allowed(
        self, make_service_spec, tmp_test_dir, monkeypatch
    ):
        monkeypatch.chdir(tmp_test_dir)
        # parse_rules accepts the pair without raising.
        DependenciesRule.parse_rules(["api -> domain/models", "api -> domain/services"])

    def test_rule_name_property(self, make_service_spec):
        assert DependenciesRule(make_service_spec()).rule_name == "internal_dependencies"

    def test_allowed_import_passes(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        (tmp_test_dir / "api").mkdir()
        (tmp_test_dir / "domain").mkdir()
        (tmp_test_dir / "api" / "views.py").write_text("from domain import models\n")

        spec = make_service_spec(dependencies=["api -> domain"])
        violations = DependenciesRule(spec).validate()

        import_errors = [v for v in violations if "Forbidden import" in v.message]
        assert len(import_errors) == 0

    def test_covered_source_forbidden_reverse_import(
        self, make_service_spec, tmp_test_dir, monkeypatch
    ):
        """domain -> api is forbidden when only api -> domain is declared."""
        monkeypatch.chdir(tmp_test_dir)
        (tmp_test_dir / "domain").mkdir()
        (tmp_test_dir / "api").mkdir()
        (tmp_test_dir / "domain" / "models.py").write_text("from api import views\n")

        spec = make_service_spec(dependencies=["api -> domain"])
        violations = DependenciesRule(spec).validate()

        import_errors = [v for v in violations if "Forbidden import" in v.message]
        assert len(import_errors) == 1
        assert "domain" in import_errors[0].details["from_module"]

    def test_stdlib_imports_ignored(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        (tmp_test_dir / "api").mkdir()
        (tmp_test_dir / "api" / "views.py").write_text(
            "import os\nimport sys\nfrom pathlib import Path\n"
        )

        spec = make_service_spec(dependencies=["api -> domain"])
        violations = DependenciesRule(spec).validate()

        import_errors = [v for v in violations if "Forbidden import" in v.message]
        assert len(import_errors) == 0

    def test_nested_paths_in_dependencies(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        controllers_dir = tmp_test_dir / "api" / "controllers"
        models_dir = tmp_test_dir / "domain" / "models"
        controllers_dir.mkdir(parents=True)
        models_dir.mkdir(parents=True)
        (controllers_dir / "user.py").write_text("from domain.models import User\n")

        spec = make_service_spec(dependencies=["api/controllers -> domain/models"])
        violations = DependenciesRule(spec).validate()

        import_errors = [v for v in violations if "Forbidden import" in v.message]
        assert len(import_errors) == 0
