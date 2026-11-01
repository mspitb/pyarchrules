"""Specification loader for pyarchrules configuration."""

from __future__ import annotations

import tomllib
from dataclasses import fields
from pathlib import Path

from pyarchrules.core.errors import ConfigError
from pyarchrules.model.spec.project_spec import ProjectSpec
from pyarchrules.model.spec.service_spec import ServiceSpec

_KNOWN_PROJECT_KEYS = frozenset({"services", "isolate_services"})

# Every ServiceSpec field except the ones derived by the loader is a TOML key.
KNOWN_SERVICE_KEYS = frozenset(f.name for f in fields(ServiceSpec)) - {"name", "project_root"}


class SpecLoader:
    """Loads the complete project specification from ``pyproject.toml``.

    Parameters
    ----------
    project_root : Path
        Directory containing ``pyproject.toml``.
    """

    def __init__(self, project_root: Path):
        self._project_root = Path(project_root).resolve()

    def load(self) -> ProjectSpec:
        """Parse ``pyproject.toml`` and return the :class:`ProjectSpec`.

        Raises
        ------
        ConfigError
            If the file cannot be read or parsed, or the configuration is invalid.
        """
        pyproject = self._project_root / "pyproject.toml"
        try:
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError) as e:
            raise ConfigError(f"Cannot read {pyproject}: {e}") from None

        config = data.get("tool", {}).get("pyarchrules", {})
        self._validate_keys(config, _KNOWN_PROJECT_KEYS, context="[tool.pyarchrules]")

        return ProjectSpec(
            services=self._parse_services(config.get("services", {})),
            isolate_services=bool(config.get("isolate_services", False)),
        )

    def _parse_services(self, services_data: dict) -> dict[str, ServiceSpec]:
        if not services_data:
            return {"root": ServiceSpec(name="root", path=".", project_root=self._project_root)}

        if not isinstance(services_data, dict):
            raise ConfigError("[tool.pyarchrules.services] must be a table")

        return {
            name: self._parse_service(name, svc_data) for name, svc_data in services_data.items()
        }

    def _parse_service(self, name: str, svc_data: dict) -> ServiceSpec:
        if not isinstance(svc_data, dict):
            raise ConfigError(
                f"Service '{name}' must be a table, got {type(svc_data).__name__}. "
                f'Use:\n  [tool.pyarchrules.services.{name}]\n  path = "..."'
            )

        self._validate_keys(
            svc_data, KNOWN_SERVICE_KEYS, context=f"[tool.pyarchrules.services.{name}]"
        )

        rel_path = svc_data.get("path")
        if rel_path is None:
            raise ConfigError(f"Service '{name}' must have 'path' key")

        rel_posix = str(rel_path).replace("\\", "/").rstrip("/") or "."
        full_path = (self._project_root / rel_posix).resolve()
        if not full_path.is_relative_to(self._project_root):
            raise ConfigError(f"Service '{name}' path is outside project root: {rel_path}")
        if not full_path.is_dir():
            raise ConfigError(f"Service '{name}' path doesn't exist: {rel_path}")

        options = {key: svc_data[key] for key in svc_data.keys() - {"path"}}
        for flag in ("tree_allow_files", "no_circular_imports", "shared"):
            if flag in options:
                options[flag] = bool(options[flag])

        return ServiceSpec(name=name, path=rel_posix, project_root=self._project_root, **options)

    @staticmethod
    def _validate_keys(data: dict, known: frozenset[str], context: str) -> None:
        """Raise :class:`ConfigError` if *data* contains keys outside *known*."""
        unknown = sorted(set(data) - known)
        if unknown:
            keys = ", ".join(f"'{k}'" for k in unknown)
            raise ConfigError(
                f"Unknown key(s) in {context}: {keys}. Known keys: {', '.join(sorted(known))}"
            )
