"""Registry for linter rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyarchrules.core.registries.base_registry import BaseRegistry
from pyarchrules.core.rules.linter import (
    AllowedServiceDependenciesRule,
    DependenciesRule,
    NoPrivateLinterRule,
    NoWildcardLinterRule,
    ServiceIsolationRule,
    TreeRule,
)

if TYPE_CHECKING:
    from pyarchrules.core.rules.rule import Rule
    from pyarchrules.model.spec.project_spec import ProjectSpec


class LinterRegistry(BaseRegistry["list[Rule]"]):
    """Registry for linter rules derived from ``pyproject.toml`` configuration.

    When a :class:`~pyarchrules.model.spec.project_spec.ProjectSpec` is supplied,
    rules are auto-registered from the spec on construction.

    Parameters
    ----------
    project_spec : ProjectSpec, optional
        When provided, rules are automatically registered for every service.
    """

    def __init__(self, project_spec: ProjectSpec | None = None) -> None:
        super().__init__()
        if project_spec is not None:
            self._load_from_spec(project_spec)

    def get(self, service_name: str) -> list[Rule]:
        """Return registered rules for *service_name*, or an empty list if absent.

        Parameters
        ----------
        service_name : str

        Returns
        -------
        list[Rule]
        """
        return self._store.get(service_name, [])

    def register(self, service_name: str, rule: Rule) -> None:
        """Register a single rule for *service_name*.

        Parameters
        ----------
        service_name : str
        rule : Rule
        """
        self._store.setdefault(service_name, []).append(rule)

    # ------------------------------------------------------------------
    # Violation collection
    # ------------------------------------------------------------------

    def _collect_violations(self) -> list:
        """Collect all violations from every registered linter rule."""
        violations = []
        for rules in self._store.values():
            for rule in rules:
                violations.extend(rule.validate())
        return violations

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_from_spec(self, project_spec: ProjectSpec) -> None:
        for service_name, service_spec in project_spec.services.items():
            rules: list[Rule] = []

            if project_spec.isolate_services:
                rules.append(ServiceIsolationRule(service_spec, project_spec))
            if service_spec.tree:
                rules.append(TreeRule(service_spec))
            if service_spec.allowed_service_dependencies:
                rules.append(AllowedServiceDependenciesRule(service_spec, project_spec))
            if service_spec.dependencies:
                rules.append(DependenciesRule(service_spec))
            if service_spec.no_wildcard_imports:
                folders = (
                    service_spec.no_wildcard_imports
                    if isinstance(service_spec.no_wildcard_imports, list)
                    else [None]
                )
                rules.extend(NoWildcardLinterRule(service_spec, folder=f) for f in folders)
            if service_spec.no_private_imports:
                folders = (
                    service_spec.no_private_imports
                    if isinstance(service_spec.no_private_imports, list)
                    else [None]
                )
                rules.extend(NoPrivateLinterRule(service_spec, folder=f) for f in folders)

            for rule in rules:
                self.register(service_name, rule)
