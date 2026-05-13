"""CLI tests for check command."""

import pytest

from pyarchrules.cli import app


@pytest.mark.cli
def test_check_command_with_no_pyproject(make_project, cli_runner):
    """Should fail with exit code 2 (config error) when pyproject.toml doesn't exist."""
    project = make_project(with_pyproject=False)

    result = cli_runner.invoke(app, ["check", str(project.root)])

    assert result.exit_code == 2
    assert "Failed to load configuration" in result.output


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
    )

    result = cli_runner.invoke(app, ["check", str(project.root), "--quiet"])

    assert result.exit_code == 0
    assert "Service: api" not in result.stdout


@pytest.mark.cli
def test_check_warns_on_nested_same_service_name(make_project, cli_runner):
    """Nested pyproject.toml that redefines a root service name → warning."""
    project = make_project(
        with_pyproject=True,
        services={"api": "services/api"},
    )
    # Nested pyproject inside services/api with its own pyarchrules table
    # defining a service called 'api'.
    project.touch(
        "services/api/pyproject.toml",
        '[project]\nname = "api"\nversion = "0.0.0"\n'
        "[tool.pyarchrules]\n"
        "[tool.pyarchrules.services.api]\n"
        'path = "."\n',
    )

    result = cli_runner.invoke(
        app, ["check", str(project.root)]
    )

    assert result.exit_code == 0
    combined = result.output
    assert "nested pyarchrules config" in combined
    assert "redefines service 'api'" in combined


@pytest.mark.cli
def test_check_warns_on_nested_same_path(make_project, cli_runner):
    """Nested pyproject.toml whose service targets the same dir → warning."""
    project = make_project(
        with_pyproject=True,
        services={"api": "services/api"},
    )
    project.touch(
        "services/api/pyproject.toml",
        '[project]\nname = "api"\nversion = "0.0.0"\n'
        "[tool.pyarchrules]\n"
        "[tool.pyarchrules.services.internal]\n"
        'path = "."\n',
    )

    result = cli_runner.invoke(
        app, ["check", str(project.root)]
    )

    assert result.exit_code == 0
    combined = result.output
    assert "same path as root service 'api'" in combined


@pytest.mark.cli
def test_check_no_warning_when_nested_clean(make_project, cli_runner):
    """No nested pyarchrules config → no nested-config message at all."""
    project = make_project(
        with_pyproject=True,
        services={"api": "services/api"},
    )
    # Nested pyproject WITHOUT [tool.pyarchrules].
    project.touch(
        "services/api/pyproject.toml",
        '[project]\nname = "api"\nversion = "0.0.0"\n',
    )

    result = cli_runner.invoke(
        app, ["check", str(project.root)]
    )

    assert result.exit_code == 0
    combined = result.output
    assert "nested pyarchrules config" not in combined


@pytest.mark.cli
def test_check_skips_hidden_dirs(make_project, cli_runner):
    """Nested config under .venv/ (or any hidden dir) is ignored."""
    project = make_project(
        with_pyproject=True,
        services={"api": "services/api"},
    )
    project.touch(
        ".venv/some_pkg/pyproject.toml",
        '[project]\nname = "vendored"\nversion = "0.0.0"\n'
        "[tool.pyarchrules]\n"
        "[tool.pyarchrules.services.api]\n"
        'path = "."\n',
    )

    result = cli_runner.invoke(
        app, ["check", str(project.root)]
    )

    assert result.exit_code == 0
    combined = result.output
    assert "nested pyarchrules config" not in combined


@pytest.mark.cli
def test_check_returns_exit_1_on_real_violation(make_project, cli_runner):
    """A missing tree path produces an error → exit code 1."""
    project = make_project(
        with_pyproject=True,
        services={"api": "services/api"},
    )
    # Append a tree requirement that won't exist on disk.
    pyproj = project.pyproject.read_text(encoding="utf-8")
    pyproj += '\n[tool.pyarchrules.services.api]\npath = "services/api"\ntree = ["does_not_exist"]\n'
    # rewrite cleanly: regenerate with extra config
    project.write_pyproject(
        {
            "project": {"name": "p", "version": "0.1.0"},
            "tool": {
                "pyarchrules": {
                    "services": {
                        "api": {
                            "path": "services/api",
                            "tree": ["does_not_exist"],
                        }
                    }
                }
            },
        }
    )
    project.mkdir("services/api")

    result = cli_runner.invoke(app, ["check", str(project.root)])

    assert result.exit_code == 1
    assert "Validation failed" in result.output


@pytest.mark.cli
def test_check_json_format_is_valid_json(make_project, cli_runner):
    """--format json prints a parseable JSON document."""
    import json

    project = make_project(
        with_pyproject=True,
        services={"api": "services/api"},
    )

    result = cli_runner.invoke(app, ["check", str(project.root), "--format", "json"])

    assert result.exit_code == 0
    # Find JSON in output (text noise may precede when verbose; here verbose
    # is suppressed for json format on the pretty-printer side, so output is
    # a clean JSON document).
    payload = json.loads(result.output.strip().splitlines()[-1] if result.output.strip().count("{") == 1 else result.output[result.output.index("{"):])
    assert "summary" in payload
    assert payload["summary"]["is_valid"] is True


@pytest.mark.cli
def test_show_config_prints_json(make_project, cli_runner):
    """show-config emits parseable JSON with services + rule names."""
    import json

    project = make_project(
        with_pyproject=True,
        services={"api": "services/api"},
    )

    result = cli_runner.invoke(app, ["show-config", str(project.root)])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert "api" in payload["services"]
    assert payload["services"]["api"]["path"] == "services/api"


@pytest.mark.cli
def test_check_service_filter_excludes_other_violations(make_project, cli_runner):
    """--service NAME hides violations from unrelated services."""
    project = make_project(
        with_pyproject=True,
        services={"api": "services/api", "worker": "services/worker"},
    )
    project.write_pyproject(
        {
            "project": {"name": "p", "version": "0.1.0"},
            "tool": {
                "pyarchrules": {
                    "services": {
                        "api": {"path": "services/api", "tree": ["nope"]},
                        "worker": {"path": "services/worker"},
                    }
                }
            },
        }
    )
    project.mkdir("services/api")
    project.mkdir("services/worker")

    # Without filter: exit 1 (api violation).
    result_all = cli_runner.invoke(app, ["check", str(project.root)])
    assert result_all.exit_code == 1

    # With --service worker: exit 0 (api violation filtered out).
    result_filtered = cli_runner.invoke(
        app, ["check", str(project.root), "--service", "worker"]
    )
    assert result_filtered.exit_code == 0


@pytest.mark.cli
def test_check_unknown_service_filter_exits_2(make_project, cli_runner):
    project = make_project(with_pyproject=True, services={"api": "services/api"})
    result = cli_runner.invoke(
        app, ["check", str(project.root), "--service", "ghost"]
    )
    assert result.exit_code == 2
    assert "Unknown service" in result.output

