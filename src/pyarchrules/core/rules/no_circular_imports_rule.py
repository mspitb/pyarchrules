"""Rule: no_circular_imports — detect cyclic module dependencies."""

from __future__ import annotations

from pyarchrules.core.rules.checks.imports import (
    build_module_graph,
    collect_imports_from_dir,
    detect_cycles,
)
from pyarchrules.core.rules.dsl import DslRule
from pyarchrules.core.rules.linter import LinterRule
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.project_spec import ProjectSpec
from pyarchrules.model.spec.service_spec import ServiceSpec


class NoCircularImportsRule(LinterRule, DslRule):
    """Report import cycles inside the service (or inside a sub-*folder* of it).

    Builds a module graph from relative and absolute imports found by AST
    parsing and reports one cycle per strongly connected component. Imports
    under ``if TYPE_CHECKING:`` are ignored.

    DSL usage::

        rules.for_service("backend").no_circular_imports()
        rules.for_service("backend").no_circular_imports("domain")

    TOML usage::

        [tool.pyarchrules.services.backend]
        no_circular_imports = true
    """

    name = "no_circular_imports"
    dsl_method = "no_circular_imports"

    def __init__(self, service_spec: ServiceSpec, folder: str | None = None):
        super().__init__(service_spec)
        self._folder = folder

    @classmethod
    def from_spec(
        cls, service_spec: ServiceSpec, project_spec: ProjectSpec
    ) -> NoCircularImportsRule | None:
        return cls(service_spec) if service_spec.no_circular_imports else None

    def _check(self) -> list[RuleViolation]:
        base = self._service_spec.absolute_path
        scan_root = base / self._folder if self._folder else base

        if not scan_root.exists():
            relative = scan_root.relative_to(self._service_spec.project_root)
            return [self._violation(f"Directory does not exist: {relative}")]

        graph = build_module_graph(collect_imports_from_dir(scan_root), scan_root)
        return [
            self._violation(
                f"Circular import detected: {' -> '.join(cycle)}", details={"cycle": cycle}
            )
            for cycle in detect_cycles(graph)
        ]
