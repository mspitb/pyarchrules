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
def test_init_project_adds_default_keys(make_project, cli_runner):
    """Should create an empty [tool.pyarchrules] section (no project-level keys in v1)."""
    project = make_project(with_pyproject=False, name="my_awesome_project")
    project.write_minimal_pyproject()

    result = cli_runner.invoke(app, ["init-project", str(project.root)])

    assert result.exit_code == 0
    config = project.get_pyarchrules_config()
    assert "project_name" not in config
    assert "description" not in config
    assert "root" not in config
    assert "validate_paths" not in config
    assert "isolate_services" not in config


@pytest.mark.cli
def test_init_project_does_not_add_deprecated_fields(make_project, cli_runner):
    """Should not add deprecated project_name or description fields."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    result = cli_runner.invoke(app, ["init-project", str(project.root)])

    assert result.exit_code == 0
    config = project.get_pyarchrules_config()
    assert "project_name" not in config
    assert "description" not in config


@pytest.mark.cli
def test_init_project_replaces_existing_values(make_project, cli_runner):
    """Should replace existing configuration with a fresh empty block."""
    project = make_project(
        with_pyproject=True,
        extra_config={},
    )
    # Manually add legacy keys to verify they get cleaned up on reinit
    data = project.read_pyproject()
    data["tool"]["pyarchrules"]["root"] = "./src"
    data["tool"]["pyarchrules"]["validate_paths"] = False
    project.write_pyproject(data)

    result = cli_runner.invoke(app, ["init-project", str(project.root)], input="y\n")

    assert result.exit_code == 0
    config = project.get_pyarchrules_config()
    assert "project_name" not in config
    assert "description" not in config
    assert "root" not in config
    assert "validate_paths" not in config
    assert "isolate_services" not in config


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
    """Should create empty [tool.pyarchrules] block when initializing (v1)."""
    project = make_project(with_pyproject=False)
    project.write_minimal_pyproject()

    result = cli_runner.invoke(app, ["init-project", str(project.root)])

    assert result.exit_code == 0
    config = project.get_pyarchrules_config()
    assert "root" not in config
    assert "validate_paths" not in config
    assert "isolate_services" not in config


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
    assert "root" not in config
    assert "isolate_services" not in config


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
    project = make_project(with_pyproject=True)

    result = cli_runner.invoke(app, ["init-project", "--force", str(project.root)])

    assert result.exit_code == 0
    # Should not show warning or prompt
    assert "already initialized" not in result.stdout
    assert "Do you want to reinitialize" not in result.stdout
    # Should be reinitialized with empty v1 block
    config = project.get_pyarchrules_config()
    assert "project_name" not in config
    assert "root" not in config
    assert "isolate_services" not in config


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
