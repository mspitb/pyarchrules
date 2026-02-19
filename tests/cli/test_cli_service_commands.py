"""CLI tests for add-service and remove-service commands."""

import os

import pytest

from pyarchrules.cli import app


@pytest.mark.cli
def test_add_service_with_arguments(make_project, cli_runner):
    """Should add service when name and path are provided as arguments."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    # Initialize first
    cwd = os.getcwd()
    try:
        os.chdir(project.root)
        cli_runner.invoke(app, ["init-project", "."])
        result = cli_runner.invoke(app, ["add-service", "api", "services/api"])
    finally:
        os.chdir(cwd)

    assert result.exit_code == 0
    assert "Added service 'api'" in result.stdout

    config = project.get_pyarchrules_config()
    assert "api" in config["services"]
    assert config["services"]["api"]["path"] == "services/api"


@pytest.mark.cli
def test_add_service_interactive_mode(make_project, cli_runner):
    """Should prompt for name and path when not provided."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    # Initialize first
    cwd = os.getcwd()
    try:
        os.chdir(project.root)
        cli_runner.invoke(app, ["init-project", "."])
        result = cli_runner.invoke(app, ["add-service"], input="billing\nservices/billing\n")
    finally:
        os.chdir(cwd)

    assert result.exit_code == 0
    assert "Service name:" in result.stdout
    assert "Service path" in result.stdout  # Don't check for exact format since default is shown
    assert "Added service 'billing'" in result.stdout

    config = project.get_pyarchrules_config()
    assert "billing" in config["services"]
    assert config["services"]["billing"]["path"] == "services/billing"


@pytest.mark.cli
def test_add_service_invalid_name(make_project, cli_runner):
    """Should reject invalid service names."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    # Initialize first
    cwd = os.getcwd()
    try:
        os.chdir(project.root)
        cli_runner.invoke(app, ["init-project", "."])
        result = cli_runner.invoke(app, ["add-service", "my-service", "services/api"])
    finally:
        os.chdir(cwd)

    assert result.exit_code == 1
    assert "Invalid service name" in result.stdout


@pytest.mark.cli
def test_add_service_replaces_existing(make_project, cli_runner):
    """Should replace/update service when it already exists."""
    project = make_project(with_pyproject=True, services={"api": "services/api"})

    cwd = os.getcwd()
    try:
        os.chdir(project.root)
        result = cli_runner.invoke(app, ["add-service", "api", "services/api_v2"])
    finally:
        os.chdir(cwd)

    assert result.exit_code == 0
    assert "updated" in result.stdout.lower()

    config = project.get_pyarchrules_config()
    # Service should be updated with new path
    assert config["services"]["api"]["path"] == "services/api_v2"


@pytest.mark.cli
def test_add_service_not_initialized(make_project, cli_runner):
    """Should fail when [tool.pyarchrules] not initialized."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    cwd = os.getcwd()
    try:
        os.chdir(project.root)
        result = cli_runner.invoke(app, ["add-service", "api", "services/api"])
    finally:
        os.chdir(cwd)

    assert result.exit_code == 1
    assert "not initialized" in result.stdout


@pytest.mark.cli
def test_remove_service_with_argument(make_project, cli_runner):
    """Should remove service when name is provided."""
    project = make_project(
        with_pyproject=True, services={"api": "services/api", "billing": "services/billing"}
    )

    cwd = os.getcwd()
    try:
        os.chdir(project.root)
        result = cli_runner.invoke(app, ["remove-service", "api", "--force"])
    finally:
        os.chdir(cwd)

    assert result.exit_code == 0
    assert "Service 'api' removed" in result.stdout

    config = project.get_pyarchrules_config()
    assert "api" not in config["services"]
    assert "billing" in config["services"]


@pytest.mark.cli
def test_remove_service_interactive_mode(make_project, cli_runner):
    """Should prompt for service name when not provided."""
    project = make_project(
        with_pyproject=True, services={"api": "services/api", "billing": "services/billing"}
    )

    cwd = os.getcwd()
    try:
        os.chdir(project.root)
        result = cli_runner.invoke(app, ["remove-service", "--force"], input="api\n")
    finally:
        os.chdir(cwd)

    assert result.exit_code == 0
    assert "Available services:" in result.stdout
    assert "Service name to remove:" in result.stdout
    assert "Service 'api' removed" in result.stdout


@pytest.mark.cli
def test_remove_service_with_confirmation(make_project, cli_runner):
    """Should ask for confirmation before removing."""
    project = make_project(with_pyproject=True, services={"api": "services/api"})

    cwd = os.getcwd()
    try:
        os.chdir(project.root)
        result = cli_runner.invoke(app, ["remove-service", "api"], input="y\n")
    finally:
        os.chdir(cwd)

    assert result.exit_code == 0
    assert "Remove service 'api'?" in result.stdout
    assert "Service 'api' removed" in result.stdout


@pytest.mark.cli
def test_remove_service_cancel_confirmation(make_project, cli_runner):
    """Should cancel when user rejects confirmation."""
    project = make_project(with_pyproject=True, services={"api": "services/api"})

    cwd = os.getcwd()
    try:
        os.chdir(project.root)
        result = cli_runner.invoke(app, ["remove-service", "api"], input="n\n")
    finally:
        os.chdir(cwd)

    assert result.exit_code == 0
    assert "Cancelled" in result.stdout

    # Service should still exist
    config = project.get_pyarchrules_config()
    assert "api" in config["services"]


@pytest.mark.cli
def test_list_services_shows_all(make_project, cli_runner):
    """Should list all configured services."""
    project = make_project(
        with_pyproject=True, services={"api": "services/api", "billing": "services/billing"}
    )

    cwd = os.getcwd()
    try:
        os.chdir(project.root)
        result = cli_runner.invoke(app, ["list-services"])
    finally:
        os.chdir(cwd)

    assert result.exit_code == 0
    assert "Configured services" in result.stdout
    assert "api" in result.stdout
    assert "billing" in result.stdout


@pytest.mark.cli
def test_list_services_empty(make_project, cli_runner):
    """Should handle empty services section gracefully."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    cwd = os.getcwd()
    try:
        os.chdir(project.root)
        # Initialize doesn't create services section
        cli_runner.invoke(app, ["init-project", "."])
        result = cli_runner.invoke(app, ["list-services"])
    finally:
        os.chdir(cwd)

    assert result.exit_code == 0
    assert "No services configured" in result.stdout


@pytest.mark.cli
def test_list_services_not_initialized(make_project, cli_runner):
    """Should fail when [tool.pyarchrules] not initialized."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    cwd = os.getcwd()
    try:
        os.chdir(project.root)
        result = cli_runner.invoke(app, ["list-services"])
    finally:
        os.chdir(cwd)

    assert result.exit_code == 1
    assert "not initialized" in result.stdout
