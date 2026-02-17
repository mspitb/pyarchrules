"""Shared pytest fixtures for pyarchrules tests."""

from __future__ import annotations

import shutil
import tempfile
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import tomlkit
from typer.testing import CliRunner

TMP_TESTS_FOLDER_NAME = ".pyarchrules-tests-tmp"


def dump_toml(data: dict[str, Any]) -> str:
    return tomlkit.dumps(data)


def load_toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


class Project:
    """Helper for creating test project structures."""

    def __init__(self, root: Path):
        self.root = root

    @property
    def pyproject(self) -> Path:
        return self.root / "pyproject.toml"

    def write_pyproject(self, data: dict[str, Any]) -> Path:
        """Write a dictionary as pyproject.toml using tomlkit."""
        self.pyproject.write_text(dump_toml(data), encoding="utf-8")
        return self.pyproject

    def write_minimal_pyproject(self, project_name: str = "test") -> Path:
        """Create a minimal pyproject.toml with just [project] section."""
        return self.write_pyproject({"project": {"name": project_name}})

    def mkdir(self, rel: str) -> Path:
        p = self.root / rel
        p.mkdir(parents=True, exist_ok=True)
        return p

    def touch(self, rel: str, content: str = "") -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def read_pyproject(self) -> dict[str, Any]:
        """Read pyproject.toml and return as dictionary."""
        return load_toml(self.pyproject)

    def get_pyarchrules_config(self) -> dict[str, Any]:
        """Get [tool.pyarchrules] section from pyproject.toml."""
        data = self.read_pyproject()
        return data.get("tool", {}).get("pyarchrules", {})


@pytest.fixture(scope="session")
def setup_tmp_dir():
    """
    Create a session-wide temporary folder for pyarchrules tests
    using tempfile.TemporaryDirectory().
    """
    # Create a TemporaryDirectory in system temp folder
    temp_dir = tempfile.TemporaryDirectory(prefix=TMP_TESTS_FOLDER_NAME + "-")
    base_tmp = Path(temp_dir.name)
    base_tmp.mkdir(exist_ok=True)

    yield base_tmp

    temp_dir.cleanup()


@pytest.fixture()
def tmp_test_dir(setup_tmp_dir, request) -> Path:
    """
    Per-test temporary folder inside the session temp folder.
    """
    test_name = request.node.name
    test_dir = setup_tmp_dir / test_name

    if test_dir.exists():
        shutil.rmtree(test_dir, ignore_errors=True)

    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


@pytest.fixture()
def make_project(tmp_test_dir: Path) -> Callable[..., Project]:
    """
    Factory fixture for creating isolated test projects in temp folder.
    """

    def _make(
        *,
        name: str = "test_project",
        with_pyproject: bool = True,
        services: dict[str, str] | None = None,
        extra_config: dict[str, Any] | None = None,
        create_service_dirs: bool = True,
    ) -> Project:
        root = tmp_test_dir / name
        root.mkdir(parents=True, exist_ok=True)

        project = Project(root=root.resolve())

        if with_pyproject:
            data: dict[str, Any] = {
                "project": {"name": name, "version": "0.1.0"},
                "tool": {"pyarchrules": {}},
            }

            if services:
                # New format: [tool.pyarchrules.services.NAME] with path = "..."
                services_table = {}
                for service_name, service_path in services.items():
                    services_table[service_name] = {"path": service_path}
                data["tool"]["pyarchrules"]["services"] = services_table
                # Create service directories if requested
                if create_service_dirs:
                    for rel_path in services.values():
                        project.mkdir(rel_path)

            if extra_config:
                data["tool"]["pyarchrules"].update(extra_config)

            project.write_pyproject(data)

        return project

    return _make


@pytest.fixture()
def cli_runner() -> CliRunner:
    return CliRunner()
