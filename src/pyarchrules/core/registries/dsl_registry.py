"""Registry for DSL-defined rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyarchrules.core.rules.rule_set import ServiceRuleSet


class DSLRegistry:
    """Registry for storing DSL-defined RuleSets per service."""

    def __init__(self):
        self._service_rules: dict[str, ServiceRuleSet] = {}

    def register(self, service_name: str, rule_set: ServiceRuleSet) -> None:
        """Register a RuleSet for a service."""
        self._service_rules[service_name] = rule_set

    def get(self, service_name: str) -> ServiceRuleSet | None:
        """Get the RuleSet for a service, or None if not registered."""
        return self._service_rules.get(service_name)

    def get_all(self) -> dict[str, ServiceRuleSet]:
        """Get all registered RuleSets."""
        return dict(self._service_rules)

    def has(self, service_name: str) -> bool:
        """Check if a service has a registered RuleSet."""
        return service_name in self._service_rules

    def clear(self) -> None:
        """Clear all registered RuleSets."""
        self._service_rules.clear()
