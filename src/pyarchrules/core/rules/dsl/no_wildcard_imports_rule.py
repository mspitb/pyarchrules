"""DSL rule: no_wildcard_imports — forbid `from x import *`."""

from __future__ import annotations

from pathlib import Path

from pyarchrules.core.rules.base.import_rule import ImportBaseRule
from pyarchrules.core.rules.checks.imports import ImportInfo
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class NoWildcardImportsRule(ImportBaseRule):
    """Forbid wildcard imports (``from x import *``) within a service or folder.

    DSL usage::

        rules.for_service("backend").no_wildcard_imports()
        rules.for_service("backend").no_wildcard_imports("api")
    """

    def __init__(self, service_spec: ServiceSpec, folder: str | None = None):
        super().__init__(service_spec, folder=folder)

    @property
    def rule_name(self) -> str:
        return "no_wildcard_imports"

    def _check_file(
        self,
        file: Path,
        rel_path: Path,
        imports: list[ImportInfo],
    ) -> list[RuleViolation]:
        return [
            self._make_violation(
                rel_path=rel_path,
                message=f"Wildcard import forbidden: "
                f"'from {imp.module} import *' (line {imp.lineno})",
                details={"module": imp.module, "lineno": imp.lineno},
            )
            for imp in imports
            if imp.is_wildcard
        ]
