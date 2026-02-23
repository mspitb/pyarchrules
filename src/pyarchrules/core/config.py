"""Configuration management for PyArchRules."""

from __future__ import annotations

from pathlib import Path

import tomlkit

from pyarchrules.core.errors import PyArchError


class PyArchConfig:
    """Manages pyproject.toml configuration for PyArchRules."""

    def __init__(self, doc: tomlkit.TOMLDocument, path: Path):
        self._doc = doc
        self._path = path

    @classmethod
    def load(cls, project_root: Path) -> PyArchConfig:
        """Load configuration from pyproject.toml."""
        pyproject = project_root / "pyproject.toml"

        if not pyproject.exists():
            raise PyArchError("pyproject.toml not found")

        with open(pyproject, encoding="utf-8") as f:
            doc = tomlkit.parse(f.read())

        return cls(doc, pyproject)

    def save(self) -> None:
        """Write configuration to pyproject.toml."""
        with open(self._path, "w", encoding="utf-8") as f:
            f.write(tomlkit.dumps(self._doc))

    def _get_pyarchrules(self) -> dict:
        """Get [tool.pyarchrules] section."""
        return self._doc.get("tool", {}).get("pyarchrules", {})

    def is_initialized(self) -> bool:
        """Check if [tool.pyarchrules] section exists."""
        return "pyarchrules" in self._doc.get("tool", {})

    def initialize(self, project_name: str, description: str | None = None) -> None:
        """Initialize [tool.pyarchrules] section with default values."""
        if description is None:
            description = "Architecture rules for this project"

        tool = self._doc.setdefault("tool", tomlkit.table())

        pyarch = tomlkit.table()
        pyarch["project_name"] = project_name
        pyarch["description"] = description
        pyarch["root"] = "."
        pyarch["validate_paths"] = True
        pyarch["isolate_services"] = True

        pyarch.add(tomlkit.nl())

        tool["pyarchrules"] = pyarch

    def get_services(self) -> dict[str, str]:
        """Get all configured services as a dict mapping name to path."""
        services = self._get_pyarchrules().get("services", {})

        if not isinstance(services, dict):
            return {}

        result = {}
        for name, service_data in services.items():
            if isinstance(service_data, dict):
                path = service_data.get("path")
                if path:
                    result[name] = str(path)
            else:
                result[name] = str(service_data)

        return result

    def add_service(self, name: str, path: str) -> None:
        """Add or update a service in the configuration."""
        if not self.is_initialized():
            raise PyArchError(
                "[tool.pyarchrules] not initialized. Run 'pyarchrules init-project' first."
            )

        if not name.isidentifier():
            raise PyArchError(f"Invalid service name '{name}'. Must be a valid Python identifier.")

        tool = self._doc.setdefault("tool", tomlkit.table())
        pyarch = tool.setdefault("pyarchrules", tomlkit.table())
        services = pyarch.setdefault("services", tomlkit.table())

        if name in services:
            del services[name]

        service_table = tomlkit.table()
        service_table["path"] = path
        service_table.add(tomlkit.nl())
        services[name] = service_table

    def remove_service(self, name: str) -> None:
        """Remove a service from the configuration."""
        if not self.is_initialized():
            raise PyArchError("[tool.pyarchrules] not initialized")

        services = self._get_pyarchrules().get("services", {})

        if name not in services:
            raise PyArchError(f"Service '{name}' not found")

        del services[name]

    def _get_project_name(self) -> str | None:
        """Get the project name from config."""
        return self._get_pyarchrules().get("project_name")

    def _get_description(self) -> str | None:
        """Get the description from config."""
        return self._get_pyarchrules().get("description")

    def _get_root(self) -> str:
        """Get the root path from config."""
        return self._get_pyarchrules().get("root", "..")

    def _get_validate_paths(self) -> bool:
        """Get the validate_paths setting from config."""
        return self._get_pyarchrules().get("validate_paths", True)
