"""Tests for DependenciesRule."""

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

    def test_invalid_arrow_direction_returns_error(self, make_service_spec):
        violations = DependenciesRule(make_service_spec(dependencies=["api <- domain"])).validate()

        assert len(violations) >= 1
        assert any("Invalid dependency rule" in v.message for v in violations)
        assert any("Invalid arrow" in v.details.get("error", "") for v in violations)

    def test_missing_arrow_returns_error(self, make_service_spec):
        violations = DependenciesRule(make_service_spec(dependencies=["api domain"])).validate()

        assert len(violations) >= 1
        assert any("Missing '->'" in v.details.get("error", "") for v in violations)

    def test_empty_source_or_target_returns_error(self, make_service_spec):
        violations = DependenciesRule(
            make_service_spec(dependencies=["-> domain", "api ->"])
        ).validate()

        assert len(violations) >= 2
        errors = [v.details.get("error", "") for v in violations]
        assert any("Empty source or target" in e for e in errors)

    def test_overlapping_rules_source_and_target(
        self, make_service_spec, tmp_test_dir, monkeypatch
    ):
        monkeypatch.chdir(tmp_test_dir)
        spec = make_service_spec(dependencies=["api -> domain", "api/controllers -> domain"])
        violations = DependenciesRule(spec).validate()

        overlap_errors = [v for v in violations if "Overlapping" in v.message]
        assert len(overlap_errors) >= 1

    def test_same_source_different_targets_allowed(
        self, make_service_spec, tmp_test_dir, monkeypatch
    ):
        monkeypatch.chdir(tmp_test_dir)
        spec = make_service_spec(dependencies=["api -> domain/models", "api -> domain/services"])
        violations = DependenciesRule(spec).validate()

        overlap_errors = [v for v in violations if "Overlapping" in v.message]
        assert len(overlap_errors) == 0

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

    def test_unspecified_imports_allowed(self, make_service_spec, tmp_test_dir, monkeypatch):
        monkeypatch.chdir(tmp_test_dir)
        (tmp_test_dir / "domain").mkdir()
        (tmp_test_dir / "api").mkdir()
        (tmp_test_dir / "domain" / "models.py").write_text("from api import views\n")

        spec = make_service_spec(dependencies=["api -> domain"])
        violations = DependenciesRule(spec).validate()

        import_errors = [v for v in violations if "Forbidden import" in v.message]
        assert len(import_errors) == 0

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
