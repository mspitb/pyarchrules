"""DSL rule: forbidden_external_libs — specific external libraries must not be imported."""

from __future__ import annotations

from pathlib import Path

from pyarchrules.core.rules.base.import_rule import ImportBaseRule
from pyarchrules.core.rules.checks.imports import STDLIB_MODULES, ImportInfo
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class ForbiddenExternalLibsRule(ImportBaseRule):
    """Forbid a folder (or the whole service) from importing specific third-party libraries.

    Only **third-party** libraries are checked. The following are never flagged:

    - Relative imports.
    - stdlib modules.
    - Imports of packages that exist as folders inside the service
      (i.e. other layers of the same project such as ``domain``, ``api``).

    DSL usage::

        rules.for_service("backend").forbidden_external_libs(libs=["django"])
        rules.for_service("backend").forbidden_external_libs("domain", libs=["django", "flask"])
    """

    def __init__(self, service_spec: ServiceSpec, libs: list[str], folder: str | None = None):
        super().__init__(service_spec, folder=folder)
        self._libs = frozenset(libs)

    @property
    def rule_name(self) -> str:
        return "forbidden_external_libs"

    def _internal_packages(self) -> frozenset[str]:
        """Return top-level folder names that are part of this service (not third-party)."""
        service_dir = self._service_spec.absolute_path
        if not service_dir.exists():
            return frozenset()
        return frozenset(
            d.name
            for d in service_dir.iterdir()
            if d.is_dir() and not d.name.startswith((".", "_"))
        )

    def _check_file(
        self,
        file: Path,
        rel_path: Path,
        imports: list[ImportInfo],
    ) -> list[RuleViolation]:
        internal = self._internal_packages()
        violations = []
        for imp in imports:
            if imp.is_relative:
                continue
            top = imp.module.split(".")[0]
            if top in STDLIB_MODULES:
                continue
            if top in internal:
                continue
            if top in self._libs:
                violations.append(
                    self._make_violation(
                        rel_path=rel_path,
                        message=f"Import of '{top}' is forbidden in this layer (line {imp.lineno})",
                        details={
                            "module": top,
                            "forbidden": sorted(self._libs),
                            "lineno": imp.lineno,
                        },
                    )
                )
        return violations
