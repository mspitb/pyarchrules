"""CLI tests for check command."""

import pytest

from pyarchrules.cli import app


@pytest.mark.cli
def test_check_command_with_no_pyproject(make_project, cli_runner):
    """Should fail when pyproject.toml doesn't exist."""
    project = make_project(with_pyproject=False)

    result = cli_runner.invoke(app, ["check", str(project.root)])

    assert result.exit_code == 1
    assert "Failed to load configuration" in result.stdout


@pytest.mark.cli
def test_check_command_with_empty_config(make_project, cli_runner):
    """Should handle empty configuration with default root service."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    result = cli_runner.invoke(app, ["check", str(project.root)])

    assert result.exit_code == 0
    assert "All checks passed" in result.stdout
    assert "root" in result.stdout


@pytest.mark.cli
def test_check_command_with_initialized_config(make_project, cli_runner):
    """Should run checks on initialized configuration."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    # Initialize with default config
    cli_runner.invoke(app, ["init-project", str(project.root)])

    # Run check
    result = cli_runner.invoke(app, ["check", str(project.root)])

    assert result.exit_code == 0
    assert "Checking" in result.stdout or "All checks passed" in result.stdout


@pytest.mark.cli
def test_check_command_with_service(make_project, cli_runner):
    """Should check service with configured rules."""
    project = make_project(
        with_pyproject=True,
        services={"api": "services/api"},
        extra_config={"root": "."},
    )

    result = cli_runner.invoke(app, ["check", str(project.root)])

    assert result.exit_code == 0
    assert "All checks passed" in result.stdout


@pytest.mark.cli
def test_check_command_verbose_output(make_project, cli_runner):
    """Should show detailed output in verbose mode."""
    project = make_project(
        with_pyproject=True,
        services={"api": "services/api"},
        extra_config={"root": "."},
    )

    result = cli_runner.invoke(app, ["check", str(project.root), "--verbose"])

    assert result.exit_code == 0
    assert "api" in result.stdout


@pytest.mark.cli
def test_check_command_quiet_output(make_project, cli_runner):
    """Should show minimal output in quiet mode."""
    project = make_project(
        with_pyproject=True,
        services={"api": "services/api"},
        extra_config={"root": "."},
    )

    result = cli_runner.invoke(app, ["check", str(project.root), "--quiet"])

    assert result.exit_code == 0
    assert "Service: api" not in result.stdout
