"""Tree structure validation rule."""

from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import Path
from typing import ClassVar

from pyarchrules.core.rules.dsl import DslRule
from pyarchrules.core.rules.linter import LinterRule
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.project_spec import ProjectSpec
from pyarchrules.model.spec.service_spec import ServiceSpec, TreeMode


class TreeRule(LinterRule, DslRule):
    """Validates directory tree structure.

    Modes (``tree_mode``)
    ---------------------
    ``"exists"`` (default):
        Only checks that every path listed in ``tree`` exists on disk.
        Anything extra is silently ignored.

    ``"strict"``:
        Every level covered by ``tree`` (service root + all intermediate
        parents up to the deepest declared path) must contain **only** the
        declared children.  Leaf directories are not inspected internally.

    ``"exact"``:
        Same as ``strict``, plus every leaf directory is walked recursively.
        Any subdirectory found inside a leaf that is not declared in ``tree``
        is reported.  Full one-to-one match of the entire tree.

    ``tree_allow_files = true`` (default):
        In ``strict`` / ``exact`` mode, loose files are always tolerated.

    ``tree_ignore``:
        List of glob patterns matched against directory basenames; matched
        dirs are exempt from ``strict`` / ``exact`` reporting (and skipped
        by leaf-walking in ``exact`` mode). Common values: ``"__snapshots__"``,
        ``"migrations"``, ``"fixtures"``.

    Config example::

        tree             = ["api", "api/model", "domain"]
        tree_mode        = "strict"
        tree_allow_files = true
        tree_ignore      = ["__snapshots__", "migrations"]
    """

    name: ClassVar[str] = "tree_structure"
    dsl_method = "tree_structure"

    @classmethod
    def from_spec(cls, service_spec: ServiceSpec, project_spec: ProjectSpec) -> TreeRule | None:
        return cls(service_spec) if service_spec.tree else None

    def _check(self) -> list[RuleViolation]:
        service_dir = self._service_spec.absolute_path
        violations = []

        # 1. All declared paths must exist (all modes)
        missing_paths = [p for p in self._service_spec.tree if not (service_dir / p).exists()]
        if missing_paths:
            violations.append(
                self._violation(
                    severity="error",
                    message=f"Missing required paths: {missing_paths}",
                    details={"missing_paths": missing_paths},
                )
            )

        mode = self._service_spec.tree_mode

        # 2. strict / exact: no extra siblings at any covered level
        if mode in (TreeMode.STRICT, TreeMode.EXACT):
            violations.extend(self._check_strict(service_dir))

        # 3. exact only: walk inside leaf directories
        if mode is TreeMode.EXACT:
            violations.extend(self._check_leaf_internals(service_dir))

        return violations

    def _check_strict(self, service_dir: Path) -> list[RuleViolation]:
        """No extra directories at any level covered by tree.

        Covered levels:
        - service root ("")
        - every intermediate ancestor of a declared path
        - every declared path that has at least one child in tree (non-leaf)

        Leaf directories are intentionally skipped here.
        """
        declared: set[str] = set(self._service_spec.tree)
        ignore_patterns = self._service_spec.tree_ignore

        covered: set[str] = {""}
        for tree_path in declared:
            parts = tree_path.split("/")
            for i in range(len(parts)):
                covered.add("/".join(parts[:i]))  # all ancestors incl. ""

        # non-leaf declared paths are also covered levels
        for tree_path in declared:
            if any(other.startswith(tree_path + "/") for other in declared):
                covered.add(tree_path)

        violations = []
        for level in sorted(covered):
            full_path = service_dir / level if level else service_dir
            if not full_path.is_dir():
                continue

            actual = {
                item.name for item in full_path.iterdir() if not item.name.startswith((".", "__"))
            }
            expected = self._direct_children(level, declared)
            extra = actual - expected

            if self._service_spec.tree_allow_files:
                extra = {i for i in extra if (full_path / i).is_dir()}

            # tree_ignore: drop any name matching one of the user's globs.
            if ignore_patterns and extra:
                extra = {name for name in extra if not _matches_any(name, ignore_patterns)}

            if extra:
                display = level or "."
                suffix = " (only folders)" if self._service_spec.tree_allow_files else ""
                violations.append(
                    self._violation(
                        severity="warning",
                        message=(
                            f"Extra items in '{display}' "
                            f"(tree_mode={self._service_spec.tree_mode.value}{suffix}): "
                            f"{sorted(extra)}"
                        ),
                        details={
                            "path": display,
                            "extra_items": sorted(extra),
                            "expected": sorted(expected),
                            "allow_files": self._service_spec.tree_allow_files,
                        },
                    )
                )

        return violations

    def _check_leaf_internals(self, service_dir: Path) -> list[RuleViolation]:
        """Walk inside every leaf directory and report undeclared subdirectories.

        A leaf is a declared path that has no children in ``tree``.
        Directory names matching any ``tree_ignore`` glob are skipped
        (the user explicitly opted them out).
        """
        declared: set[str] = set(self._service_spec.tree)
        ignore_patterns = self._service_spec.tree_ignore
        leaves = [p for p in declared if not any(o.startswith(p + "/") for o in declared)]

        undeclared: list[str] = []
        for leaf in sorted(leaves):
            leaf_path = service_dir / leaf
            if not leaf_path.is_dir():
                continue
            for dirpath in sorted(leaf_path.rglob("*")):
                if not dirpath.is_dir():
                    continue
                if dirpath.name.startswith((".", "__")):
                    continue
                if ignore_patterns and _matches_any(dirpath.name, ignore_patterns):
                    continue
                rel = dirpath.relative_to(service_dir).as_posix()
                if rel not in declared:
                    undeclared.append(rel)

        if not undeclared:
            return []

        return [
            self._violation(
                severity="warning",
                message=f"Undeclared directories inside leaf dirs (tree_mode=exact): {undeclared}",
                details={"undeclared_paths": undeclared},
            )
        ]

    @staticmethod
    def _direct_children(level: str, declared: set[str]) -> set[str]:
        """Immediate child names expected directly under *level*."""
        prefix = (level + "/") if level else ""
        children: set[str] = set()
        for path in declared:
            if path.startswith(prefix):
                rest = path[len(prefix) :]
                child = rest.split("/")[0]
                if child:
                    children.add(child)
        return children


def _matches_any(name: str, patterns: list[str]) -> bool:
    """Return ``True`` if *name* matches any of the fnmatch *patterns*."""
    return any(fnmatchcase(name, p) for p in patterns)
