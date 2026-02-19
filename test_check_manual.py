#!/usr/bin/env python3
"""Test script to verify the check command works."""

import tempfile
from pathlib import Path

import tomlkit
from typer.testing import CliRunner

from pyarchrules.cli import app


def test_check_command():
    """Test the check command with a simple configuration."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create pyproject.toml
        pyproject = project_root / "pyproject.toml"
        data = {
            "project": {"name": "test", "version": "0.1.0"},
            "tool": {
                "pyarchrules": {
                    "project_name": "test",
                    "description": "Test project",
                    "root": ".",
                    "strict": True,
                    "validate_paths": True,
                    "fail_on_warning": False,
                }
            }
        }
        pyproject.write_text(tomlkit.dumps(data))

        # Run check command
        result = runner.invoke(app, ["check", str(project_root)])

        print("Exit code:", result.exit_code)
        print("Output:")
        print(result.stdout)

        if result.exit_code != 0:
            print("FAILED!")
            if result.exception:
                raise result.exception
        else:
            print("SUCCESS!")


if __name__ == "__main__":
    test_check_command()

