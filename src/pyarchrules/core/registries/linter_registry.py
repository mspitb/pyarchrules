"""Registry for linter rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyarchrules.core.rules.rule import Rule


class LinterRegistry:
    """Registry for storing linter rules per service."""

    def __init__(self):
        self._service_rules: dict[str, list[Rule]] = {}

    def register(self, service_name: str, rule: Rule) -> None:
        """Register a rule for a service."""
        if service_name not in self._service_rules:
            self._service_rules[service_name] = []
        self._service_rules[service_name].append(rule)

    def register_many(self, service_name: str, rules: list[Rule]) -> None:
        """Register multiple rules for a service."""
        for rule in rules:
            self.register(service_name, rule)

    def get(self, service_name: str) -> list[Rule]:
        """Get all rules for a service."""
        return self._service_rules.get(service_name, [])

    def get_all(self) -> dict[str, list[Rule]]:
        """Get all registered rules grouped by service."""
        return dict(self._service_rules)

    def has(self, service_name: str) -> bool:
        """Check if a service has registered rules."""
        return service_name in self._service_rules

    def clear(self) -> None:
        """Clear all registered rules."""
        self._service_rules.clear()

    def get_all_services(self) -> list[str]:
        """Get list of all services that have registered rules."""
        return list(self._service_rules.keys())
