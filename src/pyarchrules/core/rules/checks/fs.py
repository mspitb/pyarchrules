"""File-system utility functions for architecture rules.

Pure functions — no dependency on Rule or ServiceSpec.
Used by both DSL rules (core/rules/) and linter rules (core/rules/linter/).
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

_SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def collect_files(directory: Path, pattern: str = "*") -> list[Path]:
    """Return all files directly inside *directory* matching *pattern* (non-recursive).

    Parameters
    ----------
    directory : Path
        Directory to scan (top-level only).
    pattern : str, optional
        Glob pattern to match file names against, e.g. ``"*.py"``.

    Returns
    -------
    list[Path]
        Sorted list of matching paths.
    """
    if not directory.is_dir():
        return []
    return sorted(
        p for p in directory.iterdir() if p.is_file() and fnmatch.fnmatch(p.name, pattern)
    )


def collect_files_recursive(directory: Path, pattern: str = "*") -> list[Path]:
    """Return all files under *directory* matching *pattern* (recursive).

    Parameters
    ----------
    directory : Path
        Root directory to scan.
    pattern : str, optional
        Glob pattern to match file names against.

    Returns
    -------
    list[Path]
        Sorted list of matching paths, excluding ``__pycache__``.
    """
    if not directory.is_dir():
        return []
    return sorted(
        p for p in directory.rglob(pattern) if p.is_file() and "__pycache__" not in p.parts
    )


def measure_depth(directory: Path) -> int:
    """Return the maximum directory nesting depth under *directory*.

    The root itself is depth 0; immediate subdirectories are depth 1, etc.

    Parameters
    ----------
    directory : Path
        Root directory to measure from.

    Returns
    -------
    int
        Maximum depth. Returns ``0`` when the directory is empty or missing.
    """
    if not directory.is_dir():
        return 0

    max_depth = 0
    for item in directory.rglob("*"):
        if item.is_dir() and "__pycache__" not in item.parts:
            depth = len(item.relative_to(directory).parts)
            max_depth = max(max_depth, depth)
    return max_depth


def is_snake_case_filename(name: str) -> bool:
    """Return ``True`` if *name* (without extension) is valid ``snake_case``.

    Rules: starts with a lowercase letter, contains only lowercase letters,
    digits, and underscores. Names starting with ``_`` are excluded
    (private modules are skipped from naming checks).

    Parameters
    ----------
    name : str
        File stem, e.g. ``"my_module"``.

    Returns
    -------
    bool
    """
    return bool(_SNAKE_CASE_RE.match(name))


def has_only_subdirs(directory: Path) -> tuple[bool, list[Path]]:
    """Check whether *directory* contains only subdirectories (no direct files).

    Parameters
    ----------
    directory : Path
        Directory to inspect.

    Returns
    -------
    tuple[bool, list[Path]]
        ``(True, [])`` when no files are found directly in *directory*;
        ``(False, [file, ...])`` listing the offending files otherwise.
    """
    if not directory.is_dir():
        return True, []

    files = [p for p in directory.iterdir() if p.is_file() and not p.name.startswith(".")]
    return len(files) == 0, files
