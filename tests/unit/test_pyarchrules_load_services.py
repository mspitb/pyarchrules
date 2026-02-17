"""Unit tests for PyArchRules._load_services method."""

import pytest

from pyarchrules.core.errors import PyArchError
from pyarchrules.pyarchrules import PyArchRules


@pytest.mark.unit
def test_load_services_missing_tool_section_fallback_default(make_project):
    """Missing [tool.pyarchrules] -> fallback to {'root': '.'}."""
    project = make_project(with_pyproject=False)
    project.pyproject.write_text('[project]\nname = "test"\n', encoding="utf-8")
    target = project.touch("src/app.py", "x = 1\n")

    rules = PyArchRules(str(target))
    assert rules.services == {"root": "."}


@pytest.mark.unit
def test_load_services_missing_services_table_fallback_default(make_project):
    """Missing services -> fallback to {'root': '.'}."""
    project = make_project(with_pyproject=True, services=None)
    target = project.touch("src/app.py", "x = 1\n")

    rules = PyArchRules(str(target))
    assert rules.services == {"root": "."}


@pytest.mark.unit
def test_load_services_empty_services_fallback_default(make_project):
    """Empty services -> fallback to {'root': '.'}."""
    project = make_project(with_pyproject=True, services={})
    target = project.touch("src/app.py", "x = 1\n")

    rules = PyArchRules(str(target))
    assert rules.services == {"root": "."}


@pytest.mark.unit
def test_load_services_invalid_path_backslash(make_project):
    """Backslash should be automatically normalized to forward slash."""
    project = make_project(with_pyproject=True, services={"svc": "services\\svc\\src"})
    project.mkdir("services/svc/src")
    target = project.touch("services/svc/src/app.py", "x = 1\n")

    # Should NOT raise - Path automatically normalizes backslash
    rules = PyArchRules(str(target))

    # Service path should be normalized to posix-style
    assert "svc" in rules.services
    assert rules.services["svc"] == "services/svc/src"


@pytest.mark.unit
def test_load_services_invalid_path_parent_traversal(make_project):
    project = make_project(with_pyproject=True, services={"svc": "../outside"})
    target = project.touch("src/app.py", "x = 1\n")

    with pytest.raises(PyArchError) as exc:
        PyArchRules(str(target))

    assert ".." in exc.value.message


@pytest.mark.unit
def test_load_services_path_not_found_raises(make_project):
    project = make_project(
        with_pyproject=True, services={"svc": "services/svc/src"}, create_service_dirs=False
    )
    target = project.touch("src/app.py", "x = 1\n")

    with pytest.raises(PyArchError) as exc:
        PyArchRules(str(target))

    assert "not found" in exc.value.message.lower() or "does not exist" in exc.value.message.lower()


@pytest.mark.unit
def test_load_services_single_service_validates_existing_dir(make_project):
    project = make_project(with_pyproject=True, services={"billing": "services/billing/src"})
    project.mkdir("services/billing/src")
    target = project.touch("services/billing/src/app.py", "x = 1\n")

    rules = PyArchRules(str(target))
    assert rules.services == {"billing": "services/billing/src"}


@pytest.mark.unit
def test_load_services_multiple_services(make_project):
    services = {
        "billing": "services/billing/src",
        "auth": "services/auth/src",
    }
    project = make_project(with_pyproject=True, services=services)
    project.mkdir("services/billing/src")
    project.mkdir("services/auth/src")
    target = project.touch("services/billing/src/app.py", "x = 1\n")

    rules = PyArchRules(str(target))
    assert rules.services == services


@pytest.mark.unit
def test_load_services_nonexistent_path_raises(make_project):
    """Should raise error if service path doesn't exist."""
    project = make_project(
        with_pyproject=True, services={"missing": "does/not/exist"}, create_service_dirs=False
    )

    with pytest.raises(PyArchError, match="Service 'missing' path does not exist"):
        PyArchRules(project.root)
