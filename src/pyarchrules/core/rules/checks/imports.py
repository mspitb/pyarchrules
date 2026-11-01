"""Import analysis helpers shared by the dependency, isolation and cycle rules."""

from __future__ import annotations

import ast
import os
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

STDLIB_MODULES: frozenset[str] = frozenset(sys.stdlib_module_names)

# Directories that never contain project sources worth scanning.
_SKIP_DIRS: frozenset[str] = frozenset(
    {"__pycache__", "venv", "node_modules", "build", "dist", "site-packages"}
)


def iter_py_files(root: Path) -> Iterator[Path]:
    """Yield every ``.py`` file under *root*, skipping hidden and vendored directories."""
    stack: list[str] = [str(root)]
    while stack:
        try:
            entries = list(os.scandir(stack.pop()))
        except OSError:
            continue
        for entry in entries:
            if entry.name.startswith("."):
                continue
            if entry.is_dir(follow_symlinks=False):
                if entry.name not in _SKIP_DIRS:
                    stack.append(entry.path)
            elif entry.name.endswith(".py") and entry.is_file(follow_symlinks=False):
                yield Path(entry.path)


@dataclass(frozen=True)
class ImportInfo:
    """A single import statement.

    ``module`` is kept as written, including leading dots for relative imports
    (``".models"``). ``names`` is empty for ``import x`` and lists the imported
    names for ``from x import a, b``. ``type_checking`` marks imports that live
    under ``if TYPE_CHECKING:`` and therefore never execute at runtime.
    """

    module: str
    names: tuple[str, ...] = ()
    is_relative: bool = False
    lineno: int = 0
    type_checking: bool = False


def _is_type_checking_test(test: ast.expr) -> bool:
    if isinstance(test, ast.Name):
        return test.id == "TYPE_CHECKING"
    return isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING"


def _iter_statements(body: list[ast.stmt], in_tc: bool = False) -> Iterator[tuple[ast.stmt, bool]]:
    """Yield every statement below *body* with a flag for ``if TYPE_CHECKING`` bodies.

    Expressions are never entered, which keeps large files cheap to scan.
    """
    for node in body:
        yield node, in_tc
        if isinstance(node, ast.If) and _is_type_checking_test(node.test):
            yield from _iter_statements(node.body, True)
            yield from _iter_statements(node.orelse, in_tc)
            continue
        for field in ("body", "orelse", "finalbody", "handlers", "cases"):
            children = getattr(node, field, None)
            if not isinstance(children, list):
                continue
            for child in children:
                if isinstance(child, ast.stmt):
                    yield from _iter_statements([child], in_tc)
                else:  # ExceptHandler / match_case
                    yield from _iter_statements(child.body, in_tc)


def collect_imports(path: Path) -> list[ImportInfo]:
    """Parse every import statement of a Python file.

    Returns an empty list when the file cannot be read or parsed.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, ValueError, OSError):
        return []

    imports: list[ImportInfo] = []
    for node, in_tc in _iter_statements(tree.body):
        if isinstance(node, ast.Import):
            imports.extend(
                ImportInfo(alias.name, lineno=node.lineno, type_checking=in_tc)
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            imports.append(
                ImportInfo(
                    module="." * node.level + (node.module or ""),
                    names=tuple(alias.name for alias in node.names),
                    is_relative=node.level > 0,
                    lineno=node.lineno,
                    type_checking=in_tc,
                )
            )
    return imports


def collect_imports_from_dir(directory: Path) -> dict[Path, list[ImportInfo]]:
    """Collect imports of every ``.py`` file under *directory*."""
    return {py_file: collect_imports(py_file) for py_file in iter_py_files(directory)}


def resolve_relative(module: str, package: list[str]) -> list[str] | None:
    """Resolve a relative import to absolute path parts.

    *package* is the package of the importing module: the directory parts of
    a plain module, or the directory itself for an ``__init__.py``. Returns
    ``None`` when the import climbs above the root.
    """
    dots = len(module) - len(module.lstrip("."))
    if dots - 1 > len(package):
        return None
    base = package[: len(package) - (dots - 1)]
    rest = module.lstrip(".")
    return base + rest.split(".") if rest else base


def _module_key(rel: Path) -> tuple[str, list[str]]:
    """Return the graph key of a file and the package it belongs to."""
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        return "/".join(parts[:-1]), parts[:-1]
    package = parts[:-1]
    parts[-1] = parts[-1].removesuffix(".py")
    return "/".join(parts), package


def build_module_graph(
    imports_by_file: dict[Path, list[ImportInfo]], root: Path
) -> dict[str, set[str]]:
    """Build a module dependency graph used for cycle detection.

    Nodes are POSIX paths relative to *root* without the ``.py`` suffix
    (``"domain/models"``); a package ``__init__.py`` is keyed by its directory.
    Relative and absolute imports are both followed, but only edges between
    modules that exist under *root* are kept. Absolute imports may be written
    relative to *root* (``domain.models``) or prefixed with the root directory
    name (``backend.domain.models``). Imports under ``if TYPE_CHECKING`` are
    ignored because they never run.
    """
    files: list[tuple[str, list[str], list[ImportInfo]]] = []
    for file, imps in imports_by_file.items():
        try:
            key, package = _module_key(file.relative_to(root))
        except ValueError:
            continue
        files.append((key, package, imps))

    known = {key for key, _, _ in files}
    graph: dict[str, set[str]] = {key: set() for key in known}

    for key, package, imps in files:
        for imp in imps:
            if imp.type_checking:
                continue
            for base in _base_candidates(imp, package, root.name):
                targets = _targets(base, imp.names, known)
                if targets:
                    graph[key].update(targets - {key})
                    break
    return graph


def _base_candidates(imp: ImportInfo, package: list[str], root_name: str) -> list[list[str]]:
    if imp.is_relative:
        resolved = resolve_relative(imp.module, package)
        return [resolved] if resolved is not None else []
    parts = imp.module.split(".")
    return [parts, parts[1:]] if parts[0] == root_name else [parts]


def _targets(base: list[str], names: tuple[str, ...], known: set[str]) -> set[str]:
    """Known modules reached by ``from <base> import <names>`` or ``import <base>``."""
    submodules = {"/".join([*base, n]) for n in names} & known
    if submodules:
        return submodules
    key = "/".join(base)
    return {key} if key in known else set()


def detect_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Return one representative cycle per strongly connected component.

    Uses an iterative Tarjan algorithm, so deep graphs cannot hit the
    recursion limit. Every cycle starts and ends with the same module key.
    """
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    components: list[set[str]] = []

    for start in sorted(graph):
        if start in index:
            continue
        index[start] = low[start] = len(index)
        stack.append(start)
        on_stack.add(start)
        work = [(start, iter(sorted(graph[start])))]
        while work:
            node, neighbours = work[-1]
            for nxt in neighbours:
                if nxt not in index:
                    index[nxt] = low[nxt] = len(index)
                    stack.append(nxt)
                    on_stack.add(nxt)
                    work.append((nxt, iter(sorted(graph.get(nxt, ())))))
                    break
                if nxt in on_stack:
                    low[node] = min(low[node], index[nxt])
            else:
                work.pop()
                if work:
                    parent = work[-1][0]
                    low[parent] = min(low[parent], low[node])
                if low[node] == index[node]:
                    component: set[str] = set()
                    while True:
                        member = stack.pop()
                        on_stack.discard(member)
                        component.add(member)
                        if member == node:
                            break
                    if len(component) > 1:
                        components.append(component)

    return [_shortest_cycle(graph, c) for c in sorted(components, key=min)]


def _shortest_cycle(graph: dict[str, set[str]], component: set[str]) -> list[str]:
    """Shortest cycle through the smallest node of a strongly connected component."""
    start = min(component)
    parents: dict[str, str] = {}
    queue = [start]
    for node in queue:
        for nxt in sorted(graph[node] & component):
            if nxt == start:
                chain = [node]
                while chain[-1] != start:
                    chain.append(parents[chain[-1]])
                return [*reversed(chain), start]
            if nxt not in parents:
                parents[nxt] = node
                queue.append(nxt)
    return [start, start]
