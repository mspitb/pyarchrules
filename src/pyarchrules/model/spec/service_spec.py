"""Service specification model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


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


@dataclass(slots=True, frozen=True)
class ServiceSpec:
    """Specification for a single service within the project.

    Attributes
    ----------
    name : str
        Logical service name as declared in ``pyproject.toml``.
    path : str
        Path to the service directory, relative to the project root.
    project_root : Path
        Absolute path to the project root (where ``pyproject.toml`` lives).
    tree : list[str]
        Required directory/file paths relative to the service root.
    tree_mode : TreeMode
        Controls how strictly the tree is validated.
        ``"exists"`` (default) — only presence is checked.
        ``"strict"`` — no extra dirs allowed at covered levels.
        ``"exact"`` — strict + recurse into leaf directories.
    tree_allow_files : bool
        In ``strict`` / ``exact`` mode, still permit loose files (not folders).
    tree_ignore : list[str]
        Glob patterns of directory names to skip in ``strict`` / ``exact``
        mode (e.g. ``["__snapshots__", "migrations", "fixtures"]``).
        Matched against the directory's basename via :func:`fnmatch.fnmatch`.
    dependencies : list[str]
        Internal import-flow rules, e.g. ``["api -> domain"]``.
    no_circular_imports : bool
        When ``True``, the linter registers the cycle-detection rule for this service.
    shared : bool
        When ``True``, this service is exempt from project-level
        ``isolate_services`` enforcement — other services may freely import
        from it. Typical for ``services/shared`` style common libraries.
    """

    name: str
    path: str
    project_root: Path
    tree: list[str] = field(default_factory=list)
    tree_mode: TreeMode = TreeMode.EXISTS
    tree_allow_files: bool = True
    tree_ignore: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    no_circular_imports: bool = False
    shared: bool = False

    @property
    def absolute_path(self) -> Path:
        """Absolute path to the service directory.

        Returns
        -------
        Path
            ``project_root / path``.
        """
        return self.project_root / self.path
