"""Shared pytest fixtures."""

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


class Project:
    """Test project helper."""

    def __init__(self, root: Path):
        self.root = root

    @property
    def pyproject(self) -> Path:
        return self.root / "pyproject.toml"

    def write_pyproject(self, data: dict[str, Any]) -> Path:
        self.pyproject.write_text(tomlkit.dumps(data), encoding="utf-8")
        return self.pyproject

    def write_minimal_pyproject(self, project_name: str = "test") -> Path:
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
        return tomllib.loads(self.pyproject.read_text(encoding="utf-8"))

    def get_pyarchrules_config(self) -> dict[str, Any]:
        data = self.read_pyproject()
        return data.get("tool", {}).get("pyarchrules", {})


@pytest.fixture(scope="session")
def setup_tmp_dir():
    temp_dir = tempfile.TemporaryDirectory(prefix=".pyarchrules-tests-")
    yield Path(temp_dir.name)
    temp_dir.cleanup()


@pytest.fixture()
def tmp_test_dir(setup_tmp_dir, request) -> Path:
    test_dir = setup_tmp_dir / request.node.name
    if test_dir.exists():
        shutil.rmtree(test_dir, ignore_errors=True)
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


@pytest.fixture()
def make_project(tmp_test_dir: Path) -> Callable[..., Project]:
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
                services_table = {}
                for service_name, service_path in services.items():
                    services_table[service_name] = {"path": service_path}
                data["tool"]["pyarchrules"]["services"] = services_table
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


@pytest.fixture()
def make_service_spec(tmp_test_dir: Path) -> Callable[..., Any]:
    from pyarchrules.model.spec import ServiceSpec

    def _make(name: str = "test_service", path: str = ".", **kwargs) -> ServiceSpec:
        return ServiceSpec(name=name, path=path, project_root=tmp_test_dir, **kwargs)

    return _make
