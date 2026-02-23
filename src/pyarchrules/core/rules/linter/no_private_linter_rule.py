"""Linter rule: no_private_imports — configured via pyproject.toml."""

from __future__ import annotations

from pathlib import Path

from pyarchrules.core.rules.base.import_rule import ImportBaseRule
from pyarchrules.core.rules.checks.imports import ImportInfo, has_private_import
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class NoPrivateLinterRule(ImportBaseRule):
    """Forbid importing private symbols (``_name``) configured via ``no_private_imports``.

    Activated automatically when ``no_private_imports = true`` or
    ``no_private_imports = ["folder"]`` is set in a service's TOML config.

    Parameters
    ----------
    service_spec : ServiceSpec
        Specification of the service being validated.
    folder : str, optional
        Sub-folder to restrict the scan to; ``None`` scans the whole service.
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
