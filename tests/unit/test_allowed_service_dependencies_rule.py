"""Tests for AllowedServiceDependenciesRule."""

from pyarchrules.core.rules.linter.allowed_service_dependencies_rule import (
    AllowedServiceDependenciesRule,
)
from pyarchrules.model.spec import ProjectSpec, ServiceSpec


def _make_project(tmp_path, services: dict) -> ProjectSpec:
    """Build a minimal ProjectSpec with the given services dict: {name: (path, kwargs)}."""
    specs = {}
    for name, (path, kwargs) in services.items():
        specs[name] = ServiceSpec(name=name, path=path, project_root=tmp_path, **kwargs)
    return ProjectSpec(services=specs)


class TestAllowedServiceDependenciesRule:

    def test_rule_name(self, tmp_path):
        project = _make_project(tmp_path, {"api": ("api", {})})
        rule = AllowedServiceDependenciesRule(project.services["api"], project)
        assert rule.rule_name == "allowed_service_dependencies"

    def test_no_sibling_services_passes(self, tmp_path):
        """Single-service project: no siblings to import from."""
        project = _make_project(tmp_path, {"api": ("api", {"allowed_service_dependencies": []})})
        (tmp_path / "api").mkdir()
        rule = AllowedServiceDependenciesRule(project.services["api"], project)
        assert rule.validate() == []

    def test_allowed_sibling_import_passes(self, tmp_path):
        """Importing from an explicitly allowed sibling is fine."""
        project = _make_project(
            tmp_path,
            {
                "api": ("api", {"allowed_service_dependencies": ["domain"]}),
                "domain": ("domain", {}),
            },
        )
        (tmp_path / "api").mkdir()
        (tmp_path / "api" / "views.py").write_text("from domain.models import User\n")
        (tmp_path / "domain").mkdir()

        rule = AllowedServiceDependenciesRule(project.services["api"], project)
        assert rule.validate() == []

    def test_forbidden_sibling_import_returns_error(self, tmp_path):
        """Importing from a sibling NOT in the allowlist is a violation."""
        project = _make_project(
            tmp_path,
            {
                "api": ("api", {"allowed_service_dependencies": []}),
                "domain": ("domain", {}),
            },
        )
        (tmp_path / "api").mkdir()
        (tmp_path / "api" / "views.py").write_text("from domain.models import User\n")
        (tmp_path / "domain").mkdir()

        rule = AllowedServiceDependenciesRule(project.services["api"], project)
        violations = rule.validate()

        assert len(violations) == 1
        assert violations[0].rule_name == "allowed_service_dependencies"
        assert "domain" in violations[0].details["imported_service"]

    def test_stdlib_imports_not_flagged(self, tmp_path):
        """Standard-library imports are never flagged."""
        project = _make_project(
            tmp_path,
            {
                "api": ("api", {"allowed_service_dependencies": []}),
                "os": ("os", {}),
            },
        )
        (tmp_path / "api").mkdir()
        (tmp_path / "api" / "views.py").write_text("import os\nimport sys\n")

        rule = AllowedServiceDependenciesRule(project.services["api"], project)
        assert rule.validate() == []

    def test_missing_service_dir_returns_error(self, tmp_path):
        """Missing service directory produces an error violation."""
        project = _make_project(
            tmp_path,
            {
                "api": ("api", {"allowed_service_dependencies": []}),
                "domain": ("domain", {}),
            },
        )
        # do NOT create api/ directory

        rule = AllowedServiceDependenciesRule(project.services["api"], project)
        violations = rule.validate()

        assert len(violations) == 1
        assert "does not exist" in violations[0].message

    def test_multiple_forbidden_imports_each_reported(self, tmp_path):
        """Each forbidden import produces its own violation."""
        project = _make_project(
            tmp_path,
            {
                "api": ("api", {"allowed_service_dependencies": []}),
                "domain": ("domain", {}),
                "billing": ("billing", {}),
            },
        )
        (tmp_path / "api").mkdir()
        (tmp_path / "api" / "views.py").write_text(
            "from domain.models import User\nfrom billing.invoice import Invoice\n"
        )
        (tmp_path / "domain").mkdir()
        (tmp_path / "billing").mkdir()

        rule = AllowedServiceDependenciesRule(project.services["api"], project)
        violations = rule.validate()

        assert len(violations) == 2
        imported = {v.details["imported_service"] for v in violations}
        assert imported == {"domain", "billing"}
