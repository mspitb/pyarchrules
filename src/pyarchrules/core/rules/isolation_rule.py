"""Service isolation rule — enforces cross-service import boundaries."""

from __future__ import annotations

from pyarchrules.core.rules.checks.imports import STDLIB_MODULES, collect_imports, iter_py_files
from pyarchrules.core.rules.linter import LinterRule
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.project_spec import ProjectSpec
from pyarchrules.model.spec.service_spec import ServiceSpec


class ServiceIsolationRule(LinterRule):
    """Forbid a service from importing the internals of its sibling services.

    Enabled by ``isolate_services = true`` under ``[tool.pyarchrules]``.
    Services flagged ``shared = true`` are exempt: they get no isolation rule
    and every other service may import them.

    A cross-service import is recognised by matching the top-level package
    of an absolute import against the last directory component of each
    sibling's ``path`` (``path = "services/catalog"`` → ``catalog``).

    Parameters
    ----------
    service_spec : ServiceSpec
        The service being inspected.
    project_spec : ProjectSpec
        Used to enumerate sibling services and find the ``shared`` ones.
    """

    name = "service_isolation"

    def __init__(self, service_spec: ServiceSpec, project_spec: ProjectSpec):
        super().__init__(service_spec)
        self._project_spec = project_spec

    @classmethod
    def from_spec(
        cls, service_spec: ServiceSpec, project_spec: ProjectSpec
    ) -> ServiceIsolationRule | None:
        if project_spec.isolate_services and not service_spec.shared:
            return cls(service_spec, project_spec)
        return None

    def _check(self) -> list[RuleViolation]:
        forbidden = self._forbidden_packages()
        if not forbidden:
            return []

        violations: list[RuleViolation] = []
        for py_file in iter_py_files(self._service_spec.absolute_path):
            rel_path = py_file.relative_to(self._service_spec.project_root)

            for imp in collect_imports(py_file):
                if imp.is_relative or not imp.module:
                    continue
                top = imp.module.split(".", 1)[0]
                if top in STDLIB_MODULES or top not in forbidden:
                    continue

                target_service = forbidden[top]
                violations.append(
                    self._violation(
                        f"Cross-service import in {rel_path}: "
                        f"'{imp.module}' belongs to service "
                        f"'{target_service}' (not marked shared)",
                        file=str(rel_path),
                        line=imp.lineno or None,
                        details={
                            "from_service": self._service_spec.name,
                            "to_service": target_service,
                            "import_statement": imp.module,
                        },
                    )
                )

        violations.sort(key=lambda v: (v.file or "", v.line or 0, v.message))
        return violations

    def _forbidden_packages(self) -> dict[str, str]:
        """Map importable package name → owning service for every non-shared sibling."""
        forbidden: dict[str, str] = {}
        for name, sibling in self._project_spec.services.items():
            if name == self._service_spec.name or sibling.shared:
                continue
            import_name = sibling.path.rstrip("/").split("/")[-1]
            if import_name and import_name != ".":
                forbidden[import_name] = name
        return forbidden
