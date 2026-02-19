"""Specification loader for pyarchrules configuration."""

from __future__ import annotations

import tomllib
from pathlib import Path

from pyarchrules.core.errors import PyArchError
from pyarchrules.model.spec.project_spec import ProjectSpec
from pyarchrules.model.spec.service_spec import ServiceSpec


class SpecLoader:
    """Loads the complete project specification from pyproject.toml."""

    def __init__(self, project_root: Path):
        self._project_root = Path(project_root).resolve()

    def load(self) -> ProjectSpec:
        """Load the complete project specification from pyproject.toml."""
        with open(self._project_root / "pyproject.toml", "rb") as f:
            data = tomllib.load(f)

        pyarchrules_config = data.get("tool", {}).get("pyarchrules", {})

        strict = pyarchrules_config.get("strict", True)
        validate_paths = pyarchrules_config.get("validate_paths", True)
        fail_on_warning = pyarchrules_config.get("fail_on_warning", False)

        services_data = pyarchrules_config.get("services", {})
        services = self._parse_services(services_data, validate_paths)

        return ProjectSpec(
            strict=strict,
            validate_paths=validate_paths,
            fail_on_warning=fail_on_warning,
            services=services,
        )

    def _parse_services(self, services_data: dict, validate_paths: bool) -> dict[str, ServiceSpec]:
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
            raise PyArchError("[tool.pyarchrules.services] must be a table")

        services = {}
        for name, svc_data in services_data.items():
            services[name] = self._parse_service(name, svc_data, validate_paths)

        return services

    def _parse_service(self, name: str, svc_data: dict | str, validate_paths: bool) -> ServiceSpec:
        """Parse a single service specification."""
        if isinstance(svc_data, str):
            rel_path = svc_data
            allowed_deps: list[str] = []
            tree_data: list[str] = []
            tree_strict: bool = False
            tree_allow_files: bool = True
            dependencies: list[str] = []
        else:
            rel_path = svc_data.get("path")
            if rel_path is None:
                raise PyArchError(f"Service '{name}' must have 'path' key")
            allowed_deps = svc_data.get("allowed_service_dependencies", [])
            tree_data = svc_data.get("tree", [])
            tree_strict = svc_data.get("tree_strict", False)
            tree_allow_files = svc_data.get("tree_allow_files", True)
            dependencies = svc_data.get("dependencies", [])

        rel_posix = str(rel_path).replace("\\", "/").rstrip("/") or "."
        full_path = (self._project_root / rel_posix).resolve()

        if not full_path.is_relative_to(self._project_root):
            raise PyArchError(f"Service '{name}' path is outside project root: {rel_path}")

        if validate_paths and not full_path.is_dir():
            raise PyArchError(f"Service '{name}' path doesn't exist: {rel_path}")

        return ServiceSpec(
            name=name,
            path=rel_posix,
            project_root=self._project_root,
            allowed_service_dependencies=allowed_deps,
            tree=tree_data if isinstance(tree_data, list) else [],
            tree_strict=tree_strict,
            tree_allow_files=tree_allow_files,
            dependencies=dependencies,
        )
