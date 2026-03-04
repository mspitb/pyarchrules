"""Service specification model."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


class TreeMode(StrEnum):
    """Controls how strictly the directory tree is validated.

    exists
        Only checks that every path listed in ``tree`` exists on disk.
        Anything extra is silently ignored.
    strict
        Every level covered by ``tree`` (root + all intermediate parents up to
        the deepest declared path) must contain **only** the declared children.
        Leaf directories are not inspected internally.
    exact
        Same as ``strict``, plus every leaf directory is walked recursively.
        Any subdirectory inside a leaf that is not declared in ``tree``
        is reported.  Full one-to-one match of the entire tree.
    """

    EXISTS = "exists"
    STRICT = "strict"
    EXACT = "exact"


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
    tree_mode : TreeMode
        Controls how strictly the tree is validated.
        ``"exists"`` (default) — only presence is checked.
        ``"strict"`` — no extra dirs allowed at covered levels.
        ``"full"`` — strict + recurse into leaf directories.
    tree_allow_files : bool
        In ``strict`` / ``full`` mode, still permit loose files (not folders).
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
    tree_mode: TreeMode = TreeMode.EXISTS
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
