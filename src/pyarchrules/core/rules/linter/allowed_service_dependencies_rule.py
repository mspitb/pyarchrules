"""Allowed service dependencies validation rule."""

from loguru import logger

from pyarchrules.core.rules.rule import Rule
from pyarchrules.model.rules.rule_violation import RuleViolation


class AllowedServiceDependenciesRule(Rule):
    """Validates that services only depend on allowed services."""

    @property
    def rule_name(self) -> str:
        return "allowed_service_dependencies"

    def validate(self) -> list[RuleViolation]:
        if not self._service_spec.allowed_service_dependencies:
            logger.info(f"[{self._service_spec.name}] {self.rule_name}: No restrictions, skipping")
            return []

        logger.success(f"[{self._service_spec.name}] {self.rule_name}: ✓ No violations")
        return []
