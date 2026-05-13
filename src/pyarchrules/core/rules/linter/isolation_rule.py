"""Service isolation rule — enforces cross-service import boundaries."""

from __future__ import annotations

from typing import ClassVar

from pyarchrules.core.rules.checks.imports import (
    STDLIB_MODULES,
    collect_imports,
    iter_py_files,
)
from pyarchrules.core.rules.rule import Rule
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.project_spec import ProjectSpec
from pyarchrules.model.spec.service_spec import ServiceSpec


class ServiceIsolationRule(Rule):
    """Forbid this service from importing the internals of sibling services.

    Activated when ``isolate_services = true`` is set under
    ``[tool.pyarchrules]``. Services flagged ``shared = true`` are exempt:

    - A ``shared`` service has *no* isolation rule registered (it can
      reach anywhere — it is intentionally common code).
    - A non-shared service is allowed to import from any ``shared``
      sibling, but **not** from any other non-shared sibling.

    Cross-service imports are detected by matching the top-level package
    name of each absolute import against the **last directory component**
    of each service's ``path``. E.g. ``path = "services/catalog"`` →
    import name ``catalog``. This is the convention used by every
    monorepo Python project I've seen; non-conventional layouts (e.g.
    namespace packages) may need to wait for v1.x.

    Parameters
    ----------
    service_spec : ServiceSpec
        The service being inspected.
    project_spec : ProjectSpec
        Full project specification — used to enumerate siblings and find
        out which ones are ``shared``.
    """

    # Project-level flag; CONFIG_KEYS here makes the loader accept ``shared``
    # on each individual service.
    CONFIG_KEYS: ClassVar[frozenset[str]] = frozenset({"shared"})

    def __init__(self, service_spec: ServiceSpec, project_spec: ProjectSpec):
        super().__init__(service_spec)
        self._project_spec = project_spec

    @property
    def rule_name(self) -> str:
        return "service_isolation"

    def validate(self) -> list[RuleViolation]:
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

        # Build {import_name: service_name} for every other service in the
        # project. ``shared`` siblings are skipped entirely.
        forbidden: dict[str, str] = {}
        for name, sibling in self._project_spec.services.items():
            if name == self._service_spec.name or sibling.shared:
                continue
            import_name = sibling.path.rstrip("/").split("/")[-1]
            if import_name and import_name != ".":
                forbidden[import_name] = name

        if not forbidden:
            return []

        violations: list[RuleViolation] = []
        for py_file in iter_py_files(service_dir):
            rel_path = py_file.relative_to(self._service_spec.project_root)

            for imp in collect_imports(py_file):
                if imp.is_relative or not imp.module:
                    continue
                top = imp.module.split(".", 1)[0]
                if top in STDLIB_MODULES:
                    continue
                target_service = forbidden.get(top)
                if target_service is None:
                    continue

                violations.append(
                    RuleViolation(
                        rule_name=self.rule_name,
                        service_name=self._service_spec.name,
                        severity="error",
                        message=(
                            f"Cross-service import in {rel_path}: "
                            f"'{imp.module}' belongs to service "
                            f"'{target_service}' (not marked shared)"
                        ),
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
