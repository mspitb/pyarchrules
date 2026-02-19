"""Unit tests for PyArchConfig."""

import pytest

from pyarchrules.config import PyArchConfig
from pyarchrules.core.errors import PyArchError


class TestPyArchConfigLoad:
    """Tests for PyArchConfig.load() method."""

    def test_missing_pyproject_raises_error(self, make_project):
        """Raises error when pyproject.toml doesn't exist."""
        project = make_project(with_pyproject=False)

        with pytest.raises(PyArchError, match="pyproject.toml not found"):
            PyArchConfig.load(project.root)

    def test_loads_existing_pyproject(self, make_project):
        """Loads existing pyproject.toml."""
        project = make_project(with_pyproject=False)
        project.write_minimal_pyproject()

        config = PyArchConfig.load(project.root)

        assert config is not None
        assert not config.is_initialized()


class TestPyArchConfigInitialization:
    """Tests for PyArchConfig initialization state."""

    def test_not_initialized_when_no_pyarchrules_section(self, make_project):
        """Returns False when [tool.pyarchrules] doesn't exist."""
        project = make_project(with_pyproject=False)
        project.write_minimal_pyproject()

        config = PyArchConfig.load(project.root)

        assert config.is_initialized() is False

    def test_initialized_when_pyarchrules_exists(self, make_project):
        """Returns True when [tool.pyarchrules] exists."""
        project = make_project(with_pyproject=True)

        config = PyArchConfig.load(project.root)

        assert config.is_initialized() is True

    def test_initialize_creates_config_section(self, make_project):
        """Creates [tool.pyarchrules] section."""
        project = make_project(with_pyproject=False)
        project.write_minimal_pyproject()

        config = PyArchConfig.load(project.root)
        config.initialize(project_name="test_project")
        config.save()

        data = project.read_pyproject()
        assert "tool" in data
        assert "pyarchrules" in data["tool"]
        assert data["tool"]["pyarchrules"]["project_name"] == "test_project"
        assert data["tool"]["pyarchrules"]["root"] == "."
        assert data["tool"]["pyarchrules"]["strict"] is True
        assert data["tool"]["pyarchrules"]["validate_paths"] is True
        assert data["tool"]["pyarchrules"]["fail_on_warning"] is False

    def test_initialize_with_custom_description(self, make_project):
        """Uses custom description when provided."""
        project = make_project(with_pyproject=False)
        project.write_minimal_pyproject()

        config = PyArchConfig.load(project.root)
        config.initialize(project_name="test_project", description="Custom description")
        config.save()

        data = project.read_pyproject()
        assert data["tool"]["pyarchrules"]["description"] == "Custom description"

    def test_initialize_replaces_existing_config(self, make_project):
        """Replaces existing config when called again."""
        project = make_project(with_pyproject=True, extra_config={"project_name": "old_name"})

        config = PyArchConfig.load(project.root)
        config.initialize(project_name="new_name")
        config.save()

        data = project.read_pyproject()
        assert data["tool"]["pyarchrules"]["project_name"] == "new_name"


class TestPyArchConfigServices:
    """Tests for PyArchConfig service management."""

    def test_get_services_empty_when_not_initialized(self, make_project):
        """Returns empty dict when not initialized."""
        project = make_project(with_pyproject=False)
        project.write_minimal_pyproject()

        config = PyArchConfig.load(project.root)

        assert config.get_services() == {}

    def test_get_services_returns_configured_services(self, make_project):
        """Returns all configured services."""
        project = make_project(
            with_pyproject=True,
            services={"api": "services/api", "billing": "services/billing"},
        )

        config = PyArchConfig.load(project.root)

        assert config.get_services() == {"api": "services/api", "billing": "services/billing"}

    def test_get_services_handles_simple_format(self, make_project):
        """Handles simple services = { root = "." } format."""
        project = make_project(with_pyproject=False)
        project.write_minimal_pyproject()

        config = PyArchConfig.load(project.root)
        config.initialize(project_name="test")

        # After initialization, no services table exists - services are added separately
        assert config.get_services() == {}

    def test_add_service_succeeds(self, make_project):
        """Adds a new service to configuration."""
        project = make_project(with_pyproject=True)

        config = PyArchConfig.load(project.root)
        config.add_service("api", "services/api")
        config.save()

        data = project.read_pyproject()
        assert "api" in data["tool"]["pyarchrules"]["services"]
        assert data["tool"]["pyarchrules"]["services"]["api"]["path"] == "services/api"

    def test_add_service_replaces_existing(self, make_project):
        """Replaces service if it already exists."""
        project = make_project(with_pyproject=True, services={"api": "services/api"})

        config = PyArchConfig.load(project.root)
        config.add_service("api", "services/api_v2")
        config.save()

        data = project.read_pyproject()
        assert data["tool"]["pyarchrules"]["services"]["api"]["path"] == "services/api_v2"

    def test_add_service_raises_when_not_initialized(self, make_project):
        """Raises error when not initialized."""
        project = make_project(with_pyproject=False)
        project.write_minimal_pyproject()

        config = PyArchConfig.load(project.root)

        with pytest.raises(PyArchError, match="not initialized"):
            config.add_service("api", "services/api")

    def test_remove_service_succeeds(self, make_project):
        """Removes an existing service."""
        project = make_project(
            with_pyproject=True,
            services={"api": "services/api", "billing": "services/billing"},
        )

        config = PyArchConfig.load(project.root)
        config.remove_service("api")
        config.save()

        data = project.read_pyproject()
        assert "api" not in data["tool"]["pyarchrules"]["services"]
        assert "billing" in data["tool"]["pyarchrules"]["services"]

    def test_remove_service_raises_when_not_found(self, make_project):
        """Raises error when service doesn't exist."""
        project = make_project(with_pyproject=True)

        config = PyArchConfig.load(project.root)

        with pytest.raises(PyArchError, match="Service 'nonexistent' not found"):
            config.remove_service("nonexistent")

    def test_remove_service_raises_when_not_initialized(self, make_project):
        """Raises error when not initialized."""
        project = make_project(with_pyproject=False)
        project.write_minimal_pyproject()

        config = PyArchConfig.load(project.root)

        with pytest.raises(PyArchError, match="not initialized"):
            config.remove_service("api")


class TestPyArchConfigMetadata:
    """Tests for PyArchConfig metadata (project_name, description)."""

    def test_get_project_name(self, make_project):
        """Returns project name from config."""
        project = make_project(with_pyproject=True, extra_config={"project_name": "my_project"})

        config = PyArchConfig.load(project.root)

        assert config.get_project_name() == "my_project"

    def test_get_description(self, make_project):
        """Returns description from config."""
        project = make_project(
            with_pyproject=True,
            extra_config={"description": "My custom description"},
        )

        config = PyArchConfig.load(project.root)

        assert config.get_description() == "My custom description"


class TestPyArchConfigServiceNameValidation:
    """Tests for service name validation."""

    def test_invalid_names_raise_error(self, make_project):
        """Raises error for invalid service names."""
        project = make_project(with_pyproject=True)
        config = PyArchConfig.load(project.root)

        with pytest.raises(PyArchError, match="Invalid service name"):
            config.add_service("my-service", "services/my-service")

        with pytest.raises(PyArchError, match="Invalid service name"):
            config.add_service("my service", "services/my-service")

        with pytest.raises(PyArchError, match="Invalid service name"):
            config.add_service("123service", "services/my-service")

    def test_valid_names_accepted(self, make_project):
        """Accepts valid Python identifiers as service names."""
        project = make_project(with_pyproject=True)

        config = PyArchConfig.load(project.root)
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
