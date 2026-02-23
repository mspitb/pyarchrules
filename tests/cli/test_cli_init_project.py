"""CLI tests for init-project command."""

import pytest

from pyarchrules.cli import app


@pytest.mark.cli
def test_init_project_missing_pyproject_fails(make_project, cli_runner):
    """Should fail when pyproject.toml doesn't exist."""
    project = make_project(with_pyproject=False)

    result = cli_runner.invoke(app, ["init-project", str(project.root)])

    assert result.exit_code == 1
    assert "pyproject.toml not found" in result.stdout


@pytest.mark.cli
def test_init_project_creates_tool_section(make_project, cli_runner):
    """Should create [tool.pyarchrules] section when it doesn't exist."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    result = cli_runner.invoke(app, ["init-project", str(project.root)])

    assert result.exit_code == 0
    data = project.read_pyproject()
    assert "tool" in data
    assert "pyarchrules" in data["tool"]


@pytest.mark.cli
def test_init_project_adds_project_name(make_project, cli_runner):
    """Should add project_name to [tool.pyarchrules]."""
    project = make_project(with_pyproject=False, name="my_awesome_project")
    project.write_minimal_pyproject()

    result = cli_runner.invoke(app, ["init-project", str(project.root)])

    assert result.exit_code == 0
    config = project.get_pyarchrules_config()
    assert config["project_name"] == "my_awesome_project"


@pytest.mark.cli
def test_init_project_adds_description(make_project, cli_runner):
    """Should add description to [tool.pyarchrules]."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    result = cli_runner.invoke(app, ["init-project", str(project.root)])

    assert result.exit_code == 0
    config = project.get_pyarchrules_config()
    assert "description" in config
    assert "Architecture rules" in config["description"]


@pytest.mark.cli
def test_init_project_replaces_existing_values(make_project, cli_runner):
    """Should replace existing project_name and description with fresh values."""
    project = make_project(
        with_pyproject=True,
        extra_config={"project_name": "existing_name", "description": "existing description"},
    )

    result = cli_runner.invoke(app, ["init-project", str(project.root)], input="y\n")

    assert result.exit_code == 0
    config = project.get_pyarchrules_config()
    # Values should be replaced with defaults
    assert config["project_name"] == "test_project"  # From root path name
    assert config["description"] == "Architecture rules for this project"
    assert config["root"] == "."
    assert config["isolate_services"] is True


@pytest.mark.cli
def test_init_project_success_message(make_project, cli_runner):
    """Should display success message."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    result = cli_runner.invoke(app, ["init-project", str(project.root)])

    assert result.exit_code == 0
    assert "initialized" in result.stdout.lower()
    assert "pyproject.toml" in result.stdout


@pytest.mark.cli
def test_init_project_creates_root_service(make_project, cli_runner):
    """Should create root = "." in [tool.pyarchrules] when initializing."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    result = cli_runner.invoke(app, ["init-project", str(project.root)])

    assert result.exit_code == 0
    config = project.get_pyarchrules_config()
    assert config["root"] == "."
    assert config["isolate_services"] is True


@pytest.mark.cli
def test_init_project_replaces_existing_services(make_project, cli_runner):
    """Should replace entire [tool.pyarchrules] block, removing existing services."""
    project = make_project(
        with_pyproject=True, services={"api": "services/api", "billing": "services/billing"}
    )

    result = cli_runner.invoke(app, ["init-project", str(project.root)], input="y\n")

    assert result.exit_code == 0
    config = project.get_pyarchrules_config()
    # Services should be REMOVED (replaced with fresh config)
    assert "services" not in config
    assert config["root"] == "."
    assert config["isolate_services"] is True


@pytest.mark.cli
def test_init_project_shows_warning_on_reinit(make_project, cli_runner):
    """Should show warning when [tool.pyarchrules] already exists."""
    project = make_project(with_pyproject=True)

    result = cli_runner.invoke(app, ["init-project", str(project.root)], input="y\n")

    assert result.exit_code == 0
    assert "already initialized" in result.stdout
    assert "replace the existing configuration" in result.stdout


@pytest.mark.cli
def test_init_project_cancels_on_no_confirmation(make_project, cli_runner):
    """Should cancel when user rejects confirmation on reinit."""
    project = make_project(with_pyproject=True)

    result = cli_runner.invoke(app, ["init-project", str(project.root)], input="n\n")

    assert result.exit_code == 0
    assert "Cancelled" in result.stdout
    # Config should remain unchanged
    config = project.get_pyarchrules_config()
    assert config == {}


@pytest.mark.cli
def test_init_project_force_skips_confirmation(make_project, cli_runner):
    """Should skip confirmation prompt when --force flag is used."""
    project = make_project(with_pyproject=True, extra_config={"project_name": "old_name"})

    result = cli_runner.invoke(app, ["init-project", "--force", str(project.root)])

    assert result.exit_code == 0
    # Should not show warning or prompt
    assert "already initialized" not in result.stdout
    assert "Do you want to reinitialize" not in result.stdout
    # Should be reinitialized
    config = project.get_pyarchrules_config()
    assert config["project_name"] == "test_project"
    assert config["root"] == "."
    assert config["isolate_services"] is True


@pytest.mark.cli
def test_init_project_no_prompt_on_first_init(make_project, cli_runner):
    """Should not show confirmation prompt on first initialization."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    result = cli_runner.invoke(app, ["init-project", str(project.root)])

    assert result.exit_code == 0
    assert "already initialized" not in result.stdout
    assert "Do you want to reinitialize" not in result.stdout
    assert "initialized" in result.stdout


@pytest.mark.cli
def test_init_project_adds_empty_line_after_table(make_project, cli_runner):
    """Should add an empty line after the [tool.pyarchrules] table."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    result = cli_runner.invoke(app, ["init-project", str(project.root)])

    assert result.exit_code == 0

    # Read the raw TOML file content
    content = project.pyproject.read_text(encoding="utf-8")

    # Check that there's an empty line after the last property in [tool.pyarchrules]
    # The tomlkit library adds a newline after tables
    assert "\n\n" in content, "Expected empty line after TOML table"
