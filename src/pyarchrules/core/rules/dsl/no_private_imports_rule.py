"""DSL rule: no_private_imports — forbid importing `_private` symbols from foreign modules."""

from __future__ import annotations

from pathlib import Path

from pyarchrules.core.rules.base.import_rule import ImportBaseRule
from pyarchrules.core.rules.checks.imports import ImportInfo, has_private_import
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class NoPrivateImportsRule(ImportBaseRule):
    """Forbid importing private symbols (``_name``) from other modules.

    Relative same-package imports are excluded — accessing your own private
    helpers is fine.

    DSL usage::

        rules.for_service("backend").no_private_imports()
        rules.for_service("backend").no_private_imports("api")
    """

    def __init__(self, service_spec: ServiceSpec, folder: str | None = None):
        super().__init__(service_spec, folder=folder)

    @property
    def rule_name(self) -> str:
        return "no_private_imports"

    def _check_file(
        self,
        file: Path,
        rel_path: Path,
        imports: list[ImportInfo],
    ) -> list[RuleViolation]:
        return [
            self._make_violation(
                rel_path=rel_path,
                message=f"Private import forbidden: '{imp.module}' (line {imp.lineno})",
                details={"module": imp.module, "names": imp.names, "lineno": imp.lineno},
            )
            for imp in imports
            if has_private_import(imp)
        ]
