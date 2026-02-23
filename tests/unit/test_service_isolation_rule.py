"""Tests for ServiceIsolationRule."""

from pyarchrules.core.rules.linter.service_isolation_rule import ServiceIsolationRule
from pyarchrules.model.spec import ProjectSpec, ServiceSpec


def _make_project(tmp_path, services: dict) -> ProjectSpec:
    """Build a minimal ProjectSpec. services: {name: (path, kwargs)}."""
    specs = {}
    for name, (path, kwargs) in services.items():
        specs[name] = ServiceSpec(name=name, path=path, project_root=tmp_path, **kwargs)
    return ProjectSpec(services=specs)


class TestServiceIsolationRule:

    def test_rule_name(self, tmp_path):
        project = _make_project(tmp_path, {"api": ("api", {})})
        rule = ServiceIsolationRule(project.services["api"], project)
        assert rule.rule_name == "service_isolation"

    def test_no_siblings_passes(self, tmp_path):
        """Single-service project has nothing to isolate against."""
        project = _make_project(tmp_path, {"api": ("api", {})})
        (tmp_path / "api").mkdir()
        rule = ServiceIsolationRule(project.services["api"], project)
        assert rule.validate() == []

    def test_no_cross_service_imports_passes(self, tmp_path):
        """Clean service with no sibling imports passes."""
        project = _make_project(
            tmp_path,
            {
                "api": ("api", {}),
                "domain": ("domain", {}),
            },
        )
        (tmp_path / "api").mkdir()
        (tmp_path / "api" / "views.py").write_text("import os\n")
        (tmp_path / "domain").mkdir()

        rule = ServiceIsolationRule(project.services["api"], project)
        assert rule.validate() == []

    def test_import_from_sibling_returns_error(self, tmp_path):
        """Importing a non-shared sibling service is a violation."""
        project = _make_project(
            tmp_path,
            {
                "api": ("api", {}),
                "domain": ("domain", {}),
            },
        )
        (tmp_path / "api").mkdir()
        (tmp_path / "api" / "views.py").write_text("from domain.models import User\n")
        (tmp_path / "domain").mkdir()

        rule = ServiceIsolationRule(project.services["api"], project)
        violations = rule.validate()

        assert len(violations) == 1
        assert violations[0].rule_name == "service_isolation"
        assert "domain" in violations[0].details["imported_service"]

    def test_shared_service_can_be_imported(self, tmp_path):
        """A sibling marked shared=True may be freely imported."""
        project = _make_project(
            tmp_path,
            {
                "api": ("api", {}),
                "common": ("common", {"shared": True}),
            },
        )
        (tmp_path / "api").mkdir()
        (tmp_path / "api" / "views.py").write_text("from common.utils import helper\n")
        (tmp_path / "common").mkdir()

        rule = ServiceIsolationRule(project.services["api"], project)
        assert rule.validate() == []

    def test_non_shared_sibling_still_forbidden(self, tmp_path):
        """Only shared=True unlocks cross-service imports; non-shared is still forbidden."""
        project = _make_project(
            tmp_path,
            {
                "api": ("api", {}),
                "domain": ("domain", {"shared": False}),
            },
        )
        (tmp_path / "api").mkdir()
        (tmp_path / "api" / "views.py").write_text("from domain.models import User\n")
        (tmp_path / "domain").mkdir()

        rule = ServiceIsolationRule(project.services["api"], project)
        violations = rule.validate()

        assert len(violations) == 1

    def test_missing_service_dir_returns_error(self, tmp_path):
        """Missing service directory produces an error violation."""
        project = _make_project(
            tmp_path,
            {
                "api": ("api", {}),
                "domain": ("domain", {}),
            },
        )
        # do NOT create api/ directory

        rule = ServiceIsolationRule(project.services["api"], project)
        violations = rule.validate()

        assert len(violations) == 1
        assert "does not exist" in violations[0].message

    def test_stdlib_imports_not_flagged(self, tmp_path):
        """Standard-library imports that coincidentally match a service name are ignored."""
        project = _make_project(
            tmp_path,
            {
                "api": ("api", {}),
                "os": ("os_svc", {}),
            },
        )
        (tmp_path / "api").mkdir()
        (tmp_path / "api" / "views.py").write_text("import os\n")

        rule = ServiceIsolationRule(project.services["api"], project)
        assert rule.validate() == []

    def test_multiple_violations_reported(self, tmp_path):
        """Each forbidden import from a different file is reported."""
        project = _make_project(
            tmp_path,
            {
                "api": ("api", {}),
                "domain": ("domain", {}),
            },
        )
        (tmp_path / "api").mkdir()
        (tmp_path / "api" / "a.py").write_text("from domain.models import User\n")
        (tmp_path / "api" / "b.py").write_text("from domain.repo import Repo\n")
        (tmp_path / "domain").mkdir()

        rule = ServiceIsolationRule(project.services["api"], project)
        violations = rule.validate()

        assert len(violations) == 2
