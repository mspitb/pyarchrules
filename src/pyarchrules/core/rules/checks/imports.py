"""Import-related utility functions for architecture rules.

Pure functions — no dependency on Rule or ServiceSpec.
Used by both DSL rules (core/rules/) and linter rules (core/rules/linter/).
"""

from __future__ import annotations

import ast
import os
import sys
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

STDLIB_MODULES: frozenset[str] = frozenset(sys.stdlib_module_names)

# Directory names that are never walked when looking for ``.py`` files.
# These are virtually always either vendored dependencies, build artefacts,
# or tool caches — none of which belong in an architecture scan.
_SKIP_DIRS: frozenset[str] = frozenset(
    {
        "__pycache__",
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        ".tox",
        ".nox",
        "node_modules",
        "build",
        "dist",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "site-packages",
        ".eggs",
    }
)

# Per-process AST cache. Keyed by ``(absolute_path_str, mtime_ns, size)``,
# so any in-place edit invalidates the entry automatically. The cache is
# unbounded but the typical CLI process is short-lived; long-lived consumers
# (e.g. a pytest session) can call :func:`clear_cache` between runs.
_AST_CACHE: dict[tuple[str, int, int], list[ImportInfo]] = {}  # type: ignore[name-defined]


def clear_cache() -> None:
    """Drop all cached ``collect_imports`` results.

    Useful in long-running processes (test sessions, language servers) that
    edit files between rule evaluations.
    """
    _AST_CACHE.clear()


def iter_py_files(root: Path) -> Iterator[Path]:
    """Yield every ``.py`` file under *root*, skipping common noise directories.

    Uses :func:`os.scandir` for speed and prunes the walk at every step so
    vendored / cache directories never enter the scan. Order is filesystem
    order — call ``sorted()`` on the result if you need determinism.

    Parameters
    ----------
    root : Path
        Directory to walk recursively.

    Yields
    ------
    Path
        Absolute path to each ``.py`` file.
    """
    stack: list[str] = [str(root)]
    while stack:
        current = stack.pop()
        try:
            entries = os.scandir(current)
        except OSError:
            continue
        with entries as it:
            for entry in it:
                name = entry.name
                if name.startswith("."):
                    # Hidden files/dirs (e.g. ".git", ".venv") — skip both.
                    if entry.is_dir(follow_symlinks=False) and name not in _SKIP_DIRS:
                        # Still allow the user to opt into hidden dirs that
                        # aren't on the noise list? No — hidden dirs are
                        # almost never source. Stay strict.
                        continue
                    if entry.is_file(follow_symlinks=False):
                        continue
                    continue
                if entry.is_dir(follow_symlinks=False):
                    if name in _SKIP_DIRS:
                        continue
                    stack.append(entry.path)
                elif name.endswith(".py") and entry.is_file(follow_symlinks=False):
                    yield Path(entry.path)


@dataclass
class ImportInfo:
    """Represents a single import statement found in a Python file.

    Attributes
    ----------
    module : str
        Fully qualified module string as written (e.g. ``"os.path"``, ``".models"``).
    names : list[str]
        Imported names — empty for ``import x``, populated for ``from x import a, b``.
    is_wildcard : bool
        ``True`` when the statement is ``from x import *``.
    is_relative : bool
        ``True`` when the import uses leading dots (e.g. ``from . import foo``).
    source_file : Path or None
        File the import was found in.
    lineno : int
        Line number of the import statement.
    """

    module: str
    """Fully qualified module string as written (e.g. 'os.path', '.models', 'from_pkg.sub')."""

    names: list[str] = field(default_factory=list)
    """Imported names — empty for plain `import x`, populated for `from x import a, b`."""

    is_wildcard: bool = False
    """True when the statement is `from x import *`."""

    is_relative: bool = False
    """True when the import uses leading dots (e.g. `from . import foo`)."""

    source_file: Path | None = None
    """File the import was found in."""

    lineno: int = 0
    """Line number of the import statement."""


def collect_imports(path: Path) -> list[ImportInfo]:
    """Parse all import statements from a Python file.

    Results are cached by ``(path, mtime_ns, size)``; subsequent calls with
    an unmodified file return the cached list. Call :func:`clear_cache` to
    invalidate manually.

    Parameters
    ----------
    path : Path
        Path to a ``.py`` file.

    Returns
    -------
    list[ImportInfo]
        Empty list on parse failure or I/O error.
    """
    try:
        stat = path.stat()
    except OSError:
        return []

    key = (str(path), stat.st_mtime_ns, stat.st_size)
    cached = _AST_CACHE.get(key)
    if cached is not None:
        return cached

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, OSError):
        _AST_CACHE[key] = []
        return []

    imports: list[ImportInfo] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(
                    ImportInfo(
                        module=alias.name,
                        names=[],
                        is_wildcard=False,
                        is_relative=False,
                        source_file=path,
                        lineno=node.lineno,
                    )
                )

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            level = node.level or 0
            is_relative = level > 0
            # Reconstruct with leading dots for clarity
            dotted_module = ("." * level) + module

            names = [alias.name for alias in node.names]
            is_wildcard = names == ["*"]

            imports.append(
                ImportInfo(
                    module=dotted_module,
                    names=names,
                    is_wildcard=is_wildcard,
                    is_relative=is_relative,
                    source_file=path,
                    lineno=node.lineno,
                )
            )

    _AST_CACHE[key] = imports
    return imports


def collect_imports_from_dir(directory: Path) -> dict[Path, list[ImportInfo]]:
    """Collect all imports from every ``.py`` file under a directory.

    Skips ``__pycache__``, virtualenvs, build artefacts, and other common
    noise directories — see :data:`_SKIP_DIRS`.

    Parameters
    ----------
    directory : Path
        Root directory to scan recursively.

    Returns
    -------
    dict[Path, list[ImportInfo]]
        Mapping of file path to its list of parsed imports.
    """
    return {py_file: collect_imports(py_file) for py_file in iter_py_files(directory)}


def is_private_symbol(name: str) -> bool:
    """Return ``True`` if *name* is private by convention (single leading underscore).

    Dunder names such as ``__init__`` and ``__all__`` are **not** considered private.

    Parameters
    ----------
    name : str
        An identifier, e.g. ``"_helper"``, ``"__init__"``, ``"public"``.

    Returns
    -------
    bool
    """
    return name.startswith("_") and not name.startswith("__")


def has_private_import(imp: ImportInfo) -> bool:
    """Return ``True`` if the import brings in a private symbol from a foreign module.

    Covers ``from some.module import _private`` and ``import _private_module``.
    Relative same-package imports are excluded (accessing own privates is allowed).

    Parameters
    ----------
    imp : ImportInfo
        Import statement to inspect.

    Returns
    -------
    bool
    """
    if imp.is_relative:
        return False

    # `import _module`
    top = imp.module.lstrip(".").split(".")[0]
    if is_private_symbol(top):
        return True

    # `from module import _name`
    return any(is_private_symbol(n) for n in imp.names if n != "*")


def build_module_graph(
    imports_by_file: dict[Path, list[ImportInfo]], root: Path
) -> dict[str, set[str]]:
    """Build an intra-package dependency graph for cycle detection.

    Only intra-package (relative or same-package absolute) imports are included.

    Parameters
    ----------
    imports_by_file : dict[Path, list[ImportInfo]]
        Output of :func:`collect_imports_from_dir`.
    root : Path
        The package root directory, used to derive relative module keys.

    Returns
    -------
    dict[str, set[str]]
        Mapping of module key → set of imported module keys, both expressed
        as POSIX strings relative to *root* (e.g. ``"domain/models"``).
    """
    graph: dict[str, set[str]] = {}

    for file, imps in imports_by_file.items():
        try:
            rel = file.relative_to(root)
        except ValueError:
            continue

        # Convert file path to dotted module path string
        parts = list(rel.parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1].removesuffix(".py")
        mod_key = "/".join(parts)

        graph.setdefault(mod_key, set())

        for imp in imps:
            if not imp.is_relative:
                continue
            resolved_base = _resolve_relative(imp.module, mod_key)
            if not resolved_base:
                continue

            # `from . import b` → module="." → resolved_base is the package dir.
            # Each name in `names` may refer to a sub-module; try to add those edges too.
            if imp.names and not imp.module.lstrip("."):
                # names like ["b", "c"] could be sub-modules — add both the package
                # edge and per-name edges so cycles inside the package are detected.
                graph[mod_key].add(resolved_base)
                for name in imp.names:
                    candidate = f"{resolved_base}/{name}" if resolved_base else name
                    graph[mod_key].add(candidate)
            else:
                graph[mod_key].add(resolved_base)

    return graph


def _resolve_relative(module: str, current: str) -> str | None:
    """Resolve a relative import string to an absolute module key."""
    dots = len(module) - len(module.lstrip("."))
    rest = module.lstrip(".")

    parts = current.split("/")
    # Go up `dots` levels
    parts = parts[: max(0, len(parts) - dots)]

    if rest:
        parts.append(rest.replace(".", "/"))

    return "/".join(parts) if parts else None


def detect_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Detect cycles in a directed module dependency graph using DFS.

    Parameters
    ----------
    graph : dict[str, set[str]]
        Mapping produced by :func:`build_module_graph`.

    Returns
    -------
    list[list[str]]
        Each entry is a list of module keys that form a cycle.
        Returns an empty list when no cycles exist.
    """
    visited: set[str] = set()
    stack: list[str] = []
    stack_set: set[str] = set()
    cycles: list[list[str]] = []

    def dfs(node: str) -> None:
        if node in stack_set:
            # Found a cycle — extract the loop portion
            idx = stack.index(node)
            cycles.append(stack[idx:] + [node])
            return
        if node in visited:
            return

        visited.add(node)
        stack.append(node)
        stack_set.add(node)

        for neighbour in graph.get(node, set()):
            dfs(neighbour)

        stack.pop()
        stack_set.discard(node)

    for node in list(graph.keys()):
        if node not in visited:
            dfs(node)

    return cycles
