"""Unit tests for PyArchRules main class."""

import pytest

from pyarchrules.core.errors import PyArchError
from pyarchrules.pyarchrules import PyArchRules


class TestFindProjectRoot:
    """Tests for project root detection."""

    def test_no_pyproject_raises_error(self, make_project):
        """Raises error when no pyproject.toml exists."""
        project = make_project(with_pyproject=False)

        with pytest.raises(PyArchError, match="pyproject.toml not found"):
            PyArchRules(project.root)

    def test_finds_pyproject_in_same_directory(self, make_project):
        """Finds pyproject.toml in the same directory."""
        project = make_project(with_pyproject=True, services=None)

        rules = PyArchRules(project.root)

        assert rules.project_root.resolve() == project.root.resolve()

    def test_finds_pyproject_in_ancestor_directory(self, make_project):
        """Finds pyproject.toml in an ancestor directory."""
        project = make_project(with_pyproject=True, services=None)
        nested = project.mkdir("services/billing/src/domain")

        rules = PyArchRules(nested)

        assert rules.project_root.resolve() == project.root.resolve()

    def test_finds_pyproject_deeply_nested(self, make_project):
        """Finds pyproject.toml even when deeply nested."""
        project = make_project(with_pyproject=True, services=None)
        deep_path = project.mkdir("a/b/c/d/e/f/g/h")

        rules = PyArchRules(deep_path)

        assert rules.project_root.resolve() == project.root.resolve()

    def test_uses_cwd_when_no_path_provided(self, make_project, monkeypatch):
        """Uses current working directory when no path provided."""
        project = make_project(with_pyproject=True, services=None)
        monkeypatch.chdir(project.root)

        rules = PyArchRules()

        assert rules.project_root.resolve() == project.root.resolve()


class TestServicesLoading:
    """Tests for services configuration loading."""

    def test_missing_tool_section_returns_root_service(self, make_project):
        """Missing [tool.pyarchrules] falls back to root service."""
        project = make_project(with_pyproject=False)
        project.pyproject.write_text('[project]\nname = "test"\n', encoding="utf-8")

        rules = PyArchRules(project.root)

        assert rules.services == {"root": "."}

    def test_missing_services_returns_root_service(self, make_project):
        """Missing services section falls back to root service."""
        project = make_project(with_pyproject=True, services=None)

        rules = PyArchRules(project.root)

        assert rules.services == {"root": "."}

    def test_empty_services_returns_root_service(self, make_project):
        """Empty services section falls back to root service."""
        project = make_project(with_pyproject=True, services={})

        rules = PyArchRules(project.root)

        assert rules.services == {"root": "."}

    def test_loads_single_service(self, make_project):
        """Loads a single service configuration."""
        project = make_project(with_pyproject=True, services={"api": "src/api"})
        project.mkdir("src/api")

        rules = PyArchRules(project.root)

        assert rules.services == {"api": "src/api"}

    def test_loads_multiple_services(self, make_project):
        """Loads multiple service configurations."""
        services = {"auth": "services/auth", "billing": "services/billing"}
        project = make_project(with_pyproject=True, services=services)
        project.mkdir("services/auth")
        project.mkdir("services/billing")

        rules = PyArchRules(project.root)

        assert rules.services == services

    def test_normalizes_backslash_paths(self, make_project):
        """Normalizes backslash paths to forward slash."""
        project = make_project(with_pyproject=True, services={"svc": "services\\svc\\src"})
        project.mkdir("services/svc/src")

        rules = PyArchRules(project.root)

        assert rules.services["svc"] == "services/svc/src"

    def test_path_outside_project_raises_error(self, make_project):
        """Raises error when path is outside project root."""
        project = make_project(with_pyproject=True, services={"svc": "../outside"})

        with pytest.raises(PyArchError, match="outside project root"):
            PyArchRules(project.root)

    def test_nonexistent_path_raises_error(self, make_project):
        """Raises error when service path doesn't exist."""
        project = make_project(
            with_pyproject=True,
            services={"missing": "does/not/exist"},
            create_service_dirs=False,
        )

        with pytest.raises(PyArchError, match="doesn't exist"):
            PyArchRules(project.root)


class TestForService:
    """Tests for for_service() method."""

    @pytest.fixture
    def project(self, make_project):
        """Create a project with two services."""
        project = make_project(
            with_pyproject=True,
            services={"service_a": "services/a", "service_b": "services/b"},
        )
        (project.root / "services/a/api").mkdir(parents=True)
        (project.root / "services/b/api").mkdir(parents=True)
        return project

    def test_returns_rule_set_for_existing_service(self, project):
        """Returns RuleSet for an existing service."""
        rules = PyArchRules(project.root)

        rule_set = rules.for_service("service_a")

        assert rule_set is not None

    def test_raises_error_for_unknown_service(self, project):
        """Raises error for unknown service name."""
        rules = PyArchRules(project.root)

        with pytest.raises(PyArchError) as exc:
            rules.for_service("nonexistent")

        assert "Service 'nonexistent' not found" in str(exc.value)
        assert "Available" in str(exc.value)

    def test_caches_rule_set_instance(self, project):
        """Returns same RuleSet instance for repeated calls."""
        rules = PyArchRules(project.root)

        rule_set_1 = rules.for_service("service_a")
        rule_set_2 = rules.for_service("service_a")

        assert rule_set_1 is rule_set_2


class TestDSLValidation:
    """Integration tests for DSL-based rule validation."""

    @pytest.fixture
    def project(self, make_project):
        """Create a project with two services for DSL testing."""
        project = make_project(
            with_pyproject=True,
            services={"clean": "services/clean", "cyclic": "services/cyclic"},
        )

        # clean service: a package whose modules don't import each other
        clean_pkg = project.root / "services/clean/domain"
        clean_pkg.mkdir(parents=True)
        (clean_pkg / "__init__.py").write_text("", encoding="utf-8")
        (clean_pkg / "a.py").write_text("X = 1\n", encoding="utf-8")
        (clean_pkg / "b.py").write_text("Y = 2\n", encoding="utf-8")

        # cyclic service: a <-> b form a cycle inside a package
        cyclic_pkg = project.root / "services/cyclic/domain"
        cyclic_pkg.mkdir(parents=True)
        (cyclic_pkg / "__init__.py").write_text("", encoding="utf-8")
        (cyclic_pkg / "a.py").write_text("from . import b\n", encoding="utf-8")
        (cyclic_pkg / "b.py").write_text("from . import a\n", encoding="utf-8")

        return project

    def test_clean_service_passes(self, project):
        """Passes validation when no circular imports exist."""
        rules = PyArchRules(project.root)
        rules.for_service("clean").no_circular_imports()

        result = rules.validate(raise_on_violation=False, verbose=False)

        assert result.is_valid
        assert len(result.violations) == 0

    def test_circular_imports_returns_violations(self, project):
        """Returns violations when a cycle exists."""
        rules = PyArchRules(project.root)
        rules.for_service("cyclic").no_circular_imports()

        result = rules.validate(raise_on_violation=False, verbose=False)

        assert not result.is_valid
        assert len(result.violations) >= 1
        assert all(v.rule_name == "no_circular_imports" for v in result.violations)

    def test_raise_on_violation_raises_error(self, project):
        """Raises PyArchError when raise_on_violation=True."""
        rules = PyArchRules(project.root)
        rules.for_service("cyclic").no_circular_imports()

        with pytest.raises(PyArchError) as exc:
            rules.validate(raise_on_violation=True, verbose=False)

        assert "Validation failed" in str(exc.value)

    def test_chained_calls_return_self(self, project):
        """Builder pattern allows chaining."""
        rules = PyArchRules(project.root)
        result_obj = rules.for_service("clean").no_circular_imports().no_circular_imports()
        # Two rules now registered for the same service
        assert result_obj is not None
        result = rules.validate(raise_on_violation=False, verbose=False)
        assert result.is_valid

    def test_multiple_services_validation(self, project):
        """Validates multiple services in a single validate() call."""
        rules = PyArchRules(project.root)
        rules.for_service("clean").no_circular_imports()
        rules.for_service("cyclic").no_circular_imports()

        result = rules.validate(raise_on_violation=False, verbose=False)

        assert not result.is_valid
        for v in result.violations:
            assert v.service_name == "cyclic"
