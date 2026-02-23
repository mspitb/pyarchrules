"""Naming-convention utility functions for architecture rules.

Pure functions — no dependency on Rule or ServiceSpec.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path


def collect_class_names(path: Path) -> list[str]:
    """Return all top-level class names defined in a Python file.

    Parameters
    ----------
    path : Path
        Path to a ``.py`` file.

    Returns
    -------
    list[str]
        Class name strings. Empty list on parse failure.
    """
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, OSError):
        return []

    return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]


def matches_pattern(name: str, pattern: str) -> bool:
    """Return ``True`` if *name* fully matches the regexp *pattern*.

    Parameters
    ----------
    name : str
        The string to test, e.g. ``"UserService"``.
    pattern : str
        A regular expression pattern, e.g. ``r".*Service$"``.

    Returns
    -------
    bool
    """
    return bool(re.fullmatch(pattern, name))
