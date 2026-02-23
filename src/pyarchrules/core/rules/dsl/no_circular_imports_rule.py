"""DSL rule: no_circular_imports — detect cyclic module dependencies."""

from __future__ import annotations

from pathlib import Path

from pyarchrules.core.rules.base.import_rule import ImportBaseRule
from pyarchrules.core.rules.checks.imports import (
    ImportInfo,
    build_module_graph,
    collect_imports_from_dir,
    detect_cycles,
)
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class NoCircularImportsRule(ImportBaseRule):
    """Detect circular import chains within the service (or a specific *folder*).

    Uses AST parsing + DFS to build an intra-package dependency graph and find cycles.

    DSL usage::

        rules.for_service("backend").no_circular_imports()
        rules.for_service("backend").no_circular_imports("domain")
    """

    def __init__(self, service_spec: ServiceSpec, folder: str | None = None):
        super().__init__(service_spec, folder=folder)

    @property
    def rule_name(self) -> str:
        return "no_circular_imports"

    def validate(self) -> list[RuleViolation]:
        scan_root = self._resolve_scan_root()
        if not scan_root.exists():
            return [
                RuleViolation(
                    rule_name=self.rule_name,
                    service_name=self._service_spec.name,
                    severity="error",
                    message=f"Directory does not exist: "
                    f"{scan_root.relative_to(self._service_spec.project_root)}",
                )
            ]

        imports_by_file = collect_imports_from_dir(scan_root)
        graph = build_module_graph(imports_by_file, scan_root)
        cycles = detect_cycles(graph)

        return [
            RuleViolation(
                rule_name=self.rule_name,
                service_name=self._service_spec.name,
                severity="error",
                message=f"Circular import detected: {' -> '.join(cycle)}",
                details={"cycle": cycle},
            )
            for cycle in cycles
        ]

    def _check_file(
        self,
        file: Path,
        rel_path: Path,
        imports: list[ImportInfo],
    ) -> list[RuleViolation]:
        # Not used — validate() is overridden above.
        return []  # pragma: no cover
