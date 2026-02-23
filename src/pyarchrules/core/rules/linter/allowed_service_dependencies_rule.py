"""Allowed service dependencies validation rule."""

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


class AllowedServiceDependenciesRule(Rule):
    """Validates that a service only imports from explicitly allowed sibling services.

    ``allowed_service_dependencies`` is a whitelist of service names this service
    may import from. Any import whose top-level package matches another known
    service that is **not** on the whitelist is a violation.

    Parameters
    ----------
    service_spec : ServiceSpec
        Specification of the service being validated.
    project_spec : ProjectSpec
        Full project specification, used to resolve sibling service folder names.
    """

    def __init__(self, service_spec: ServiceSpec, project_spec: ProjectSpec) -> None:
        super().__init__(service_spec)
        self._project_spec = project_spec

    @property
    def rule_name(self) -> str:
        return "allowed_service_dependencies"

    def validate(self) -> list[RuleViolation]:
        """Scan all ``.py`` files and flag imports of forbidden sibling services.

        Returns
        -------
        list[RuleViolation]
        """
        allowed: set[str] = set(self._service_spec.allowed_service_dependencies)

        # Build a map of top-level folder name → service name for every OTHER service
        other_services: dict[str, str] = {}
        for svc_name, svc_spec in self._project_spec.services.items():
            if svc_name == self._service_spec.name:
                continue
            # The top-level import name is the first segment of the service path
            top_level = Path(svc_spec.path).parts[0] if svc_spec.path != "." else svc_name
            other_services[top_level] = svc_name

        if not other_services:
            logger.info(f"[{self._service_spec.name}] {self.rule_name}: No sibling services")
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

                if top not in other_services:
                    continue

                imported_service = other_services[top]
                if imported_service not in allowed:
                    violations.append(
                        RuleViolation(
                            rule_name=self.rule_name,
                            service_name=self._service_spec.name,
                            severity="error",
                            message=(
                                f"Forbidden service import in {rel_path}: "
                                f"'{imp.module}' belongs to service '{imported_service}'"
                            ),
                            details={
                                "file": str(rel_path),
                                "imported_service": imported_service,
                                "import_statement": imp.module,
                                "allowed": sorted(allowed),
                            },
                        )
                    )

        if not violations:
            logger.success(f"[{self._service_spec.name}] {self.rule_name}: ✓ No violations")

        return violations
