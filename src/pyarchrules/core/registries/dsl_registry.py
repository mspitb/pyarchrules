"""Registry for DSL-defined rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyarchrules.core.registries.base_registry import BaseRegistry
from pyarchrules.core.rules.rule_set import ServiceRuleSet

if TYPE_CHECKING:
    from pyarchrules.model.spec.project_spec import ProjectSpec


class DSLRegistry(BaseRegistry):
    """Registry for DSL-defined :class:`~pyarchrules.core.rules.rule_set.ServiceRuleSet` objects.

    One ``ServiceRuleSet`` is pre-registered per service defined in the
    :class:`~pyarchrules.model.spec.project_spec.ProjectSpec`.

    Parameters
    ----------
    project_spec : ProjectSpec
        Full project specification; one :class:`ServiceRuleSet` is created per service.
    """

    def __init__(self, project_spec: ProjectSpec) -> None:
        super().__init__()
        for service_name, service_spec in project_spec.services.items():
            self._store[service_name] = ServiceRuleSet(service_spec)

    def collect_violations(self) -> list:
        violations = []
        for rule_set in self._store.values():
            violations.extend(rule_set.collect_violations())
        return violations
