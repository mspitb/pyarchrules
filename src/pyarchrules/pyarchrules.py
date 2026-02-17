from __future__ import annotations

import tomllib
from pathlib import Path

from pyarchrules.core.errors import PyArchError


class PyArchRules:
    def __init__(self, path: str | Path):
        # Allow passing Path or str
        path = Path(path).resolve()
        if path.is_file():
            path = path.parent

        self.project_root: Path = self._find_project_root(path)
        self.services: dict[str, str] = self._load_services()

    def _find_project_root(self, start: Path) -> Path:
        current = start
        while True:
            pyproject = current / "pyproject.toml"
            if pyproject.exists():
                return current

            if current.parent == current:
                raise PyArchError("pyproject.toml not found in current or parent directories")

            current = current.parent

    def _load_services(self) -> dict[str, str]:
        pyproject_file = self.project_root / "pyproject.toml"

        with open(pyproject_file, "rb") as f:
            data = tomllib.load(f)

        pyarchrules_config = data.get("tool", {}).get("pyarchrules", {})
        services = pyarchrules_config.get("services")

        if not services:
            return {"root": "."}

        if not isinstance(services, dict):
            raise PyArchError("[tool.pyarchrules.services] must be a table")

        resolved: dict[str, str] = {}
        for name, service_data in services.items():
            # Support both nested tables and simple key=value format
            if isinstance(service_data, dict):
                rel_path = service_data.get("path")
                if rel_path is None:
                    raise PyArchError(f"Service '{name}' must have 'path' key")
            else:
                rel_path = service_data

            rel_posix = str(rel_path).replace("\\", "/").rstrip("/") or "."
            full_path = (self.project_root / rel_posix).resolve()

            try:
                full_path.relative_to(self.project_root.resolve())
            except ValueError:
                raise PyArchError(f"Service '{name}' path is outside project root: {rel_path}")

            if not full_path.exists() or not full_path.is_dir():
                raise PyArchError(
                    f"Service '{name}' path does not exist or is not a directory: {rel_path}"
                )

            resolved[name] = rel_posix

        return resolved
