"""Unit tests for PyArchRules root detection and service loading."""

import pytest

from pyarchrules.core.errors import PyArchError
from pyarchrules.pyarchrules import PyArchRules


@pytest.mark.unit
def test_find_root_no_pyproject_raises(make_project):
    """Should raise if no pyproject.toml exists anywhere."""
    project = make_project(with_pyproject=False)

    with pytest.raises(
        PyArchError, match="pyproject.toml not found in current or parent directories"
    ):
        PyArchRules(project.root)


@pytest.mark.unit
def test_find_root_pyproject_in_same_dir(make_project):
    """Should find pyproject.toml in the same directory."""
    project = make_project(with_pyproject=True, services=None)

    rules = PyArchRules(project.root)

    assert rules.project_root.resolve() == project.root.resolve()
    assert rules.services == {"root": "."}


@pytest.mark.unit
def test_find_root_pyproject_in_ancestor(make_project):
    """Should find pyproject.toml in an ancestor directory."""
    project = make_project(with_pyproject=True, services=None)

    nested = project.mkdir("services/billing/src/domain")

    rules = PyArchRules(nested)

    assert rules.project_root.resolve() == project.root.resolve()
    assert rules.services == {"root": "."}


@pytest.mark.unit
def test_find_root_multiple_levels_deep(make_project):
    """Should find pyproject.toml even when folder is deeply nested."""
    project = make_project(with_pyproject=True, services=None)

    deep_path = project.mkdir("a/b/c/d/e/f/g/h")
    rules = PyArchRules(deep_path)

    assert rules.project_root.resolve() == project.root.resolve()
    assert rules.services == {"root": "."}


@pytest.mark.unit
def test_load_services_single_service(make_project):
    """Should load a single service from pyproject.toml."""
    project = make_project(with_pyproject=True, services={"api": "src/api"})
    project.mkdir("src/api")

    rules = PyArchRules(project.root)

    assert rules.project_root.resolve() == project.root.resolve()
    assert rules.services == {"api": "src/api"}


@pytest.mark.unit
def test_load_services_multiple_services(make_project):
    """Should load multiple services from pyproject.toml."""
    project = make_project(
        with_pyproject=True,
        services={
            "auth": "services/auth",
            "billing": "services/billing",
            "notifications": "services/notifications",
        },
    )
    project.mkdir("services/auth")
    project.mkdir("services/billing")
    project.mkdir("services/notifications")

    rules = PyArchRules(project.root)

    assert rules.project_root.resolve() == project.root.resolve()
    assert rules.services == {
        "auth": "services/auth",
        "billing": "services/billing",
        "notifications": "services/notifications",
    }


@pytest.mark.unit
def test_load_services_root_service(make_project):
    """Should handle service pointing to project root (.)."""
    project = make_project(with_pyproject=True, services={"root": "."})

    rules = PyArchRules(project.root)

    assert rules.project_root.resolve() == project.root.resolve()
    assert rules.services == {"root": "."}
