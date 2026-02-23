"""Service specification model."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class ServiceSpec(BaseModel):
    """Specification for a single service within the project.

    Attributes
    ----------
    name : str
        Logical service name as declared in ``pyproject.toml``.
    path : str
        Path to the service directory, relative to the project root.
    project_root : Path
        Absolute path to the project root (where ``pyproject.toml`` lives).
    allowed_service_dependencies : list[str]
        Other service names this service is allowed to depend on.
    tree : list[str]
        Required directory/file paths relative to the service root.
    tree_strict : bool
        When ``True``, no extra items are allowed beyond those listed in *tree*.
    tree_allow_files : bool
        When *tree_strict* is ``True``, still permit loose files (not folders).
    dependencies : list[str]
        Internal import-flow rules, e.g. ``["api -> domain"]``.
    no_wildcard_imports : bool or list[str]
        ``True`` enforces the rule service-wide; a list restricts it to those folders.
    no_private_imports : bool or list[str]
        ``True`` enforces the rule service-wide; a list restricts it to those folders.
    shared : bool
        When ``True`` this service may be imported by other services.
        Used together with the project-level ``isolate_services`` flag.
    """

    name: str
    path: str
    project_root: Path
    allowed_service_dependencies: list[str] = Field(default_factory=list)
    tree: list[str] = Field(default_factory=list)
    tree_strict: bool = False
    tree_allow_files: bool = True
    dependencies: list[str] = Field(default_factory=list)
    no_wildcard_imports: bool | list[str] = False
    no_private_imports: bool | list[str] = False
    shared: bool = False

    model_config = {"arbitrary_types_allowed": True}

    @property
    def absolute_path(self) -> Path:
        """Absolute path to the service directory.

        Returns
        -------
        Path
            ``project_root / path``.
        """
        return self.project_root / self.path
