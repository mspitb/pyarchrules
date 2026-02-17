"""Unit tests for PyArchConfig."""

import pytest

from pyarchrules.config import PyArchConfig
from pyarchrules.core.errors import PyArchError


@pytest.mark.unit
def test_load_missing_pyproject_raises(make_project):
    """Should raise if pyproject.toml doesn't exist."""
    project = make_project(with_pyproject=False)

    with pytest.raises(PyArchError, match="pyproject.toml not found"):
        PyArchConfig.load(project.root)


@pytest.mark.unit
def test_load_existing_pyproject(make_project):
    """Should load existing pyproject.toml."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    config = PyArchConfig.load(project.root)

    assert config is not None
    assert not config.is_initialized()


@pytest.mark.unit
def test_is_initialized_false_when_no_pyarchrules(make_project):
    """Should return False when [tool.pyarchrules] doesn't exist."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    config = PyArchConfig.load(project.root)

    assert config.is_initialized() is False


@pytest.mark.unit
def test_is_initialized_true_when_pyarchrules_exists(make_project):
    """Should return True when [tool.pyarchrules] exists."""
    project = make_project(with_pyproject=True)

    config = PyArchConfig.load(project.root)

    assert config.is_initialized() is True


@pytest.mark.unit
def test_initialize_creates_config(make_project):
    """Should create [tool.pyarchrules] section."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    config = PyArchConfig.load(project.root)
    config.initialize(project_name="test_project")
    config.save()

    # Reload and verify
    data = project.read_pyproject()
    assert "tool" in data
    assert "pyarchrules" in data["tool"]
    assert data["tool"]["pyarchrules"]["project_name"] == "test_project"
    assert "services" in data["tool"]["pyarchrules"]
    assert data["tool"]["pyarchrules"]["services"]["root"] == "."


@pytest.mark.unit
def test_initialize_with_custom_description(make_project):
    """Should use custom description when provided."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    config = PyArchConfig.load(project.root)
    config.initialize(project_name="test_project", description="Custom description")
    config.save()

    data = project.read_pyproject()
    assert data["tool"]["pyarchrules"]["description"] == "Custom description"


@pytest.mark.unit
def test_initialize_replaces_existing_config(make_project):
    """Should replace existing config when called again."""
    project = make_project(with_pyproject=True, extra_config={"project_name": "old_name"})

    config = PyArchConfig.load(project.root)
    config.initialize(project_name="new_name")
    config.save()

    data = project.read_pyproject()
    assert data["tool"]["pyarchrules"]["project_name"] == "new_name"


@pytest.mark.unit
def test_get_services_empty_when_not_initialized(make_project):
    """Should return empty dict when not initialized."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    config = PyArchConfig.load(project.root)

    assert config.get_services() == {}


@pytest.mark.unit
def test_get_services_returns_configured_services(make_project):
    """Should return all configured services."""
    project = make_project(
        with_pyproject=True, services={"api": "services/api", "billing": "services/billing"}
    )

    config = PyArchConfig.load(project.root)
    services = config.get_services()

    assert services == {"api": "services/api", "billing": "services/billing"}


@pytest.mark.unit
def test_get_services_handles_simple_format(make_project):
    """Should handle simple services = { root = "." } format."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    config = PyArchConfig.load(project.root)
    config.initialize(project_name="test")

    services = config.get_services()

    assert services == {"root": "."}


@pytest.mark.unit
def test_add_service_succeeds(make_project):
    """Should add a new service to configuration."""
    project = make_project(with_pyproject=True)

    config = PyArchConfig.load(project.root)
    config.add_service("api", "services/api")
    config.save()

    data = project.read_pyproject()
    assert "api" in data["tool"]["pyarchrules"]["services"]
    assert data["tool"]["pyarchrules"]["services"]["api"]["path"] == "services/api"


@pytest.mark.unit
def test_add_service_replaces_existing(make_project):
    """Should replace service if it already exists."""
    project = make_project(with_pyproject=True, services={"api": "services/api"})

    config = PyArchConfig.load(project.root)

    # Add with same name but different path - should replace
    config.add_service("api", "services/api_v2")
    config.save()

    data = project.read_pyproject()
    assert "api" in data["tool"]["pyarchrules"]["services"]
    assert data["tool"]["pyarchrules"]["services"]["api"]["path"] == "services/api_v2"


@pytest.mark.unit
def test_add_service_raises_if_not_initialized(make_project):
    """Should raise if [tool.pyarchrules] not initialized."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    config = PyArchConfig.load(project.root)

    with pytest.raises(PyArchError, match="not initialized"):
        config.add_service("api", "services/api")


@pytest.mark.unit
def test_remove_service_succeeds(make_project):
    """Should remove an existing service."""
    project = make_project(
        with_pyproject=True, services={"api": "services/api", "billing": "services/billing"}
    )

    config = PyArchConfig.load(project.root)
    config.remove_service("api")
    config.save()

    data = project.read_pyproject()
    assert "api" not in data["tool"]["pyarchrules"]["services"]
    assert "billing" in data["tool"]["pyarchrules"]["services"]


@pytest.mark.unit
def test_remove_service_raises_if_not_found(make_project):
    """Should raise if service doesn't exist."""
    project = make_project(with_pyproject=True)

    config = PyArchConfig.load(project.root)

    with pytest.raises(PyArchError, match="Service 'nonexistent' not found"):
        config.remove_service("nonexistent")


@pytest.mark.unit
def test_remove_service_raises_if_not_initialized(make_project):
    """Should raise if [tool.pyarchrules] not initialized."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    config = PyArchConfig.load(project.root)

    with pytest.raises(PyArchError, match="not initialized"):
        config.remove_service("api")


@pytest.mark.unit
def test_get_project_name(make_project):
    """Should return project name from config."""
    project = make_project(with_pyproject=True, extra_config={"project_name": "my_project"})

    config = PyArchConfig.load(project.root)

    assert config.get_project_name() == "my_project"


@pytest.mark.unit
def test_get_description(make_project):
    """Should return description from config."""
    project = make_project(
        with_pyproject=True, extra_config={"description": "My custom description"}
    )

    config = PyArchConfig.load(project.root)

    assert config.get_description() == "My custom description"


@pytest.mark.unit
def test_add_service_invalid_name_raises(make_project):
    """Should raise if service name is not a valid Python identifier."""
    project = make_project(with_pyproject=True)

    config = PyArchConfig.load(project.root)

    with pytest.raises(PyArchError, match="Invalid service name"):
        config.add_service("my-service", "services/my-service")

    with pytest.raises(PyArchError, match="Invalid service name"):
        config.add_service("my service", "services/my-service")

    with pytest.raises(PyArchError, match="Invalid service name"):
        config.add_service("123service", "services/my-service")


@pytest.mark.unit
def test_add_service_valid_names(make_project):
    """Should accept valid Python identifiers as service names."""
    project = make_project(with_pyproject=True)

    config = PyArchConfig.load(project.root)

    # These should all work
    config.add_service("api", "services/api")
    config.add_service("billing_service", "services/billing")
    config.add_service("web2", "services/web2")
    config.add_service("_private", "services/private")
    config.save()

    services = config.get_services()
    assert "api" in services
    assert "billing_service" in services
    assert "web2" in services
    assert "_private" in services
