"""Specification loader for pyarchrules configuration."""

from __future__ import annotations

import tomllib
from pathlib import Path

from pyarchrules.core.errors import PyArchError
from pyarchrules.model.spec.project_spec import ProjectSpec
from pyarchrules.model.spec.service_spec import ServiceSpec, TreeMode

_KNOWN_PROJECT_KEYS = frozenset(
    {
        "root",
        "validate_paths",
        "isolate_services",
        "services",
    }
)

_KNOWN_SERVICE_KEYS = frozenset(
    {
        "path",
        "allowed_service_dependencies",
        "tree",
        "tree_mode",
        "tree_allow_files",
        "dependencies",
        "no_wildcard_imports",
        "no_private_imports",
        "shared",
    }
)


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

        validate_paths = pyarchrules_config.get("validate_paths", True)
        isolate_services = pyarchrules_config.get("isolate_services", False)
        root = pyarchrules_config.get("root", ".")

        root_path = (self._project_root / root).resolve()
        if not root_path.is_relative_to(self._project_root):
            raise PyArchError(f"'root' path is outside the project root: {root}")

        services_data = pyarchrules_config.get("services", {})
        services = self._parse_services(services_data, validate_paths, root_path)

        return ProjectSpec(
            validate_paths=validate_paths,
            isolate_services=isolate_services,
            services=services,
        )

    def _parse_services(
        self, services_data: dict, validate_paths: bool, root_path: Path
    ) -> dict[str, ServiceSpec]:
        """Parse services section from configuration."""
        if not services_data:
            return {
                "root": ServiceSpec(
                    name="root",
                    path=".",
                    project_root=root_path,
                )
            }

        if not isinstance(services_data, dict):
            raise PyArchError("[tool.pyarchrules.services] must be a table")

        return {
            name: self._parse_service(name, svc_data, validate_paths, root_path)
            for name, svc_data in services_data.items()
        }

    def _parse_service(
        self, name: str, svc_data: dict | str, validate_paths: bool, root_path: Path
    ) -> ServiceSpec:
        """Parse a single service specification."""
        if isinstance(svc_data, str):
            rel_path = svc_data
            allowed_deps: list[str] = []
            tree_data: list[str] = []
            tree_mode: TreeMode = TreeMode.EXISTS
            tree_allow_files: bool = True
            dependencies: list[str] = []
            no_wildcard_imports: bool | list[str] = False
            no_private_imports: bool | list[str] = False
            shared: bool = False
        else:
            self._validate_keys(
                svc_data,
                _KNOWN_SERVICE_KEYS,
                context=f"[tool.pyarchrules.services.{name}]",
            )
            rel_path = svc_data.get("path")
            if rel_path is None:
                raise PyArchError(f"Service '{name}' must have 'path' key")
            allowed_deps = svc_data.get("allowed_service_dependencies", [])
            tree_data = svc_data.get("tree", [])
            raw_mode = svc_data.get("tree_mode", TreeMode.EXISTS.value)
            try:
                tree_mode = TreeMode(raw_mode)
            except ValueError:
                valid = ", ".join(f'"{m.value}"' for m in TreeMode)
                raise PyArchError(
                    f"Service '{name}': invalid tree_mode '{raw_mode}'. Valid values: {valid}"
                )
            tree_allow_files = svc_data.get("tree_allow_files", True)
            dependencies = svc_data.get("dependencies", [])
            no_wildcard_imports = svc_data.get("no_wildcard_imports", False)
            no_private_imports = svc_data.get("no_private_imports", False)
            shared = svc_data.get("shared", False)

        rel_posix = str(rel_path).replace("\\", "/").rstrip("/") or "."
        full_path = (root_path / rel_posix).resolve()

        if not full_path.is_relative_to(self._project_root):
            raise PyArchError(f"Service '{name}' path is outside project root: {rel_path}")

        if validate_paths and not full_path.is_dir():
            raise PyArchError(f"Service '{name}' path doesn't exist: {rel_path}")

        return ServiceSpec(
            name=name,
            path=rel_posix,
            project_root=root_path,
            allowed_service_dependencies=allowed_deps,
            tree=tree_data if isinstance(tree_data, list) else [],
            tree_mode=tree_mode,
            tree_allow_files=tree_allow_files,
            dependencies=dependencies,
            no_wildcard_imports=no_wildcard_imports,
            no_private_imports=no_private_imports,
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
            raise PyArchError(
                f"Unknown key(s) in {context}: {keys}. Known keys: {', '.join(sorted(known))}"
            )
