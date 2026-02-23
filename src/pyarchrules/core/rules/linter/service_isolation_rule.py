"""Service isolation rule — enforces that services do not import each other."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from pyarchrules.core.rules.checks.imports import STDLIB_MODULES, collect_imports
from pyarchrules.core.rules.rule import Rule
from pyarchrules.model.rules.rule_violation import RuleViolation

if TYPE_CHECKING:
    from pyarchrules.model.spec.project_spec import ProjectSpec
    from pyarchrules.model.spec.service_spec import ServiceSpec


class ServiceIsolationRule(Rule):
    """Ensures a service does not import from any other non-shared sibling service.

    Activated automatically when ``isolate_services = true`` is set in
    ``[tool.pyarchrules]``. A service marked ``shared = true`` may be freely
    imported by other services and is excluded from the isolation check.

    Parameters
    ----------
    service_spec : ServiceSpec
        The service being scanned for illegal cross-service imports.
    project_spec : ProjectSpec
        Full project spec; used to resolve sibling service folder names and
        their ``shared`` flag.
    """

    def __init__(self, service_spec: ServiceSpec, project_spec: ProjectSpec) -> None:
        super().__init__(service_spec)
        self._project_spec = project_spec

    @property
    def rule_name(self) -> str:
        return "service_isolation"

    def validate(self) -> list[RuleViolation]:
        """Scan all ``.py`` files and flag imports of non-shared sibling services.

        Returns
        -------
        list[RuleViolation]
        """
        # Build map: top-level folder → service name, only for non-shared services
        forbidden_services: dict[str, str] = {}
        for svc_name, svc_spec in self._project_spec.services.items():
            if svc_name == self._service_spec.name:
                continue
            if svc_spec.shared:
                continue  # shared services may be imported freely
            top_level = Path(svc_spec.path).parts[0] if svc_spec.path != "." else svc_name
            forbidden_services[top_level] = svc_name

        if not forbidden_services:
            logger.info(
                f"[{self._service_spec.name}] {self.rule_name}: "
                "No non-shared sibling services to check"
            )
            return []

        service_dir = self._service_spec.absolute_path
        if not service_dir.exists():
            return [
                RuleViolation(
                    rule_name=self.rule_name,
                    service_name=self._service_spec.name,
                    severity="error",
                    message=f"Service directory does not exist: {self._service_spec.path}",
                )
            ]

        violations = []

        for py_file in sorted(service_dir.rglob("*.py")):
            if "__pycache__" in py_file.parts:
                continue

            rel_path = py_file.relative_to(service_dir)

            for imp in collect_imports(py_file):
                if imp.is_relative:
                    continue

                top = imp.module.split(".")[0]
                if top in STDLIB_MODULES:
                    continue

                if top not in forbidden_services:
                    continue

                imported_service = forbidden_services[top]
                violations.append(
                    RuleViolation(
                        rule_name=self.rule_name,
                        service_name=self._service_spec.name,
                        severity="error",
                        message=(
                            f"Isolation violation in {rel_path}: "
                            f"'{imp.module}' belongs to service '{imported_service}' "
                            f"which is not marked as shared"
                        ),
                        details={
                            "file": str(rel_path),
                            "imported_service": imported_service,
                            "import_statement": imp.module,
                            "tip": f"Add 'shared = true' to service '{imported_service}' "
                            f"in pyproject.toml to allow this import",
                        },
                    )
                )

        if not violations:
            logger.success(f"[{self._service_spec.name}] {self.rule_name}: ✓ No violations")

        return violations
