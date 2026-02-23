"""DSL rule: no_relative_imports_in — forbid relative imports in a layer or the whole service."""

from __future__ import annotations

from pathlib import Path

from pyarchrules.core.rules.base.import_rule import ImportBaseRule
from pyarchrules.core.rules.checks.imports import ImportInfo
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class NoRelativeImportsRule(ImportBaseRule):
    """Forbid relative imports (``from . import ...``) within *folder* or the whole service.

    DSL usage::

        rules.for_service("backend").no_relative_imports_in()           # whole service
        rules.for_service("backend").no_relative_imports_in("api")      # scoped to api/
    """

    def __init__(self, service_spec: ServiceSpec, folder: str | None = None):
        super().__init__(service_spec, folder=folder)

    @property
    def rule_name(self) -> str:
        return "no_relative_imports"

    def _check_file(
        self,
        file: Path,
        rel_path: Path,
        imports: list[ImportInfo],
    ) -> list[RuleViolation]:
        return [
            self._make_violation(
                rel_path=rel_path,
                message=f"Relative import forbidden: '{imp.module}' (line {imp.lineno})",
                details={"module": imp.module, "lineno": imp.lineno},
            )
            for imp in imports
            if imp.is_relative
        ]
