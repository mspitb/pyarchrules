"""Specification loader for pyarchrules configuration."""

from __future__ import annotations

import tomllib
from pathlib import Path

from pyarchrules.core.errors import ConfigError
from pyarchrules.core.registries.linter_registry import LinterRegistry
from pyarchrules.core.rules.linter.dependencies_rule import DependenciesRule
from pyarchrules.model.spec.project_spec import ProjectSpec
from pyarchrules.model.spec.service_spec import ServiceSpec, TreeMode

_KNOWN_PROJECT_KEYS = frozenset({"services", "isolate_services"})


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
        """Parse ``pyproject.toml`` and return the full
        :class:`~pyarchrules.model.spec.project_spec.ProjectSpec`.

        Returns
        -------
        ProjectSpec
            Fully populated project specification.

        Raises
        ------
        PyArchError
            If the file cannot be read or the configuration is invalid.
        """
        with open(self._project_root / "pyproject.toml", "rb") as f:
            data = tomllib.load(f)

        pyarchrules_config = data.get("tool", {}).get("pyarchrules", {})

        self._validate_keys(
            pyarchrules_config,
            _KNOWN_PROJECT_KEYS,
            context="[tool.pyarchrules]",
        )

        services_data = pyarchrules_config.get("services", {})
        services = self._parse_services(services_data)

        isolate_services = bool(pyarchrules_config.get("isolate_services", False))
        return ProjectSpec(services=services, isolate_services=isolate_services)

    def _parse_services(self, services_data: dict) -> dict[str, ServiceSpec]:
        """Parse services section from configuration."""
        if not services_data:
            return {
                "root": ServiceSpec(
                    name="root",
                    path=".",
                    project_root=self._project_root,
                )
            }

        if not isinstance(services_data, dict):
            raise ConfigError("[tool.pyarchrules.services] must be a table")

        return {
            name: self._parse_service(name, svc_data) for name, svc_data in services_data.items()
        }

    def _parse_service(self, name: str, svc_data: dict) -> ServiceSpec:
        """Parse a single service specification."""
        if not isinstance(svc_data, dict):
            raise ConfigError(
                f"Service '{name}' must be a table, got {type(svc_data).__name__}. "
                f'Use:\n  [tool.pyarchrules.services.{name}]\n  path = "..."'
            )

        self._validate_keys(
            svc_data,
            LinterRegistry.known_service_keys(),
            context=f"[tool.pyarchrules.services.{name}]",
        )

        rel_path = svc_data.get("path")
        if rel_path is None:
            raise ConfigError(f"Service '{name}' must have 'path' key")

        tree_data = svc_data.get("tree", [])
        if not isinstance(tree_data, list):
            tree_data = []
        # Reject duplicates eagerly — declaring the same path twice in
        # ``tree`` is always a typo and would silently double-process.
        if tree_data:
            seen: set[str] = set()
            duplicates: list[str] = []
            for entry in tree_data:
                if entry in seen and entry not in duplicates:
                    duplicates.append(entry)
                seen.add(entry)
            if duplicates:
                raise ConfigError(f"Service '{name}': duplicate entries in 'tree': {duplicates}")

        raw_mode = svc_data.get("tree_mode", TreeMode.EXISTS.value)
        try:
            tree_mode = TreeMode(raw_mode)
        except ValueError:
            valid = ", ".join(f'"{m.value}"' for m in TreeMode)
            raise ConfigError(
                f"Service '{name}': invalid tree_mode '{raw_mode}'. Valid values: {valid}"
            )
        tree_allow_files = svc_data.get("tree_allow_files", True)
        tree_ignore = svc_data.get("tree_ignore", [])
        if not isinstance(tree_ignore, list) or not all(isinstance(p, str) for p in tree_ignore):
            raise ConfigError(f"Service '{name}': 'tree_ignore' must be a list of glob strings")
        dependencies = svc_data.get("dependencies", [])
        no_circular_imports = svc_data.get("no_circular_imports", False)
        shared = bool(svc_data.get("shared", False))

        if dependencies:
            if not isinstance(dependencies, list):
                raise ConfigError(f"Service '{name}': 'dependencies' must be a list of strings")
            # Syntactic validation at load time. Overlap detection happens
            # at validate() time and is reported as a warning, not a config
            # error.
            DependenciesRule.parse_rules(dependencies, service_name=name)

        rel_posix = str(rel_path).replace("\\", "/").rstrip("/") or "."
        full_path = (self._project_root / rel_posix).resolve()

        if not full_path.is_relative_to(self._project_root):
            raise ConfigError(f"Service '{name}' path is outside project root: {rel_path}")

        if not full_path.is_dir():
            raise ConfigError(f"Service '{name}' path doesn't exist: {rel_path}")

        return ServiceSpec(
            name=name,
            path=rel_posix,
            project_root=self._project_root,
            tree=tree_data,
            tree_mode=tree_mode,
            tree_allow_files=tree_allow_files,
            tree_ignore=list(tree_ignore),
            dependencies=dependencies,
            no_circular_imports=bool(no_circular_imports),
            shared=shared,
        )

    @staticmethod
    def _validate_keys(data: dict, known: frozenset[str], context: str) -> None:
        """Raise :class:`~pyarchrules.core.errors.PyArchError` if *data* contains unknown keys.

        Parameters
        ----------
        data : dict
            The TOML table to inspect.
        known : frozenset[str]
            Set of permitted key names.
        context : str
            Human-readable table path used in the error message, e.g.
            ``"[tool.pyarchrules]"`` or ``"[tool.pyarchrules.services.api]"``.

        Raises
        ------
        PyArchError
            When one or more unknown keys are found.
        """
        unknown = sorted(set(data) - known)
        if unknown:
            keys = ", ".join(f"'{k}'" for k in unknown)
            raise ConfigError(
                f"Unknown key(s) in {context}: {keys}. Known keys: {', '.join(sorted(known))}"
            )
