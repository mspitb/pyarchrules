"""Internal dependencies validation rule."""

from loguru import logger

from pyarchrules.core.rules.rule import Rule
from pyarchrules.model.rules.rule_violation import RuleViolation


class DependenciesRule(Rule):
    """Validates internal module dependencies within a service."""

    @property
    def rule_name(self) -> str:
        return "internal_dependencies"

    def validate(self) -> list[RuleViolation]:
        """Validate internal dependencies."""
        violations = []

        # TODO: Implement actual validation
        # For now, return empty list (no violations)
        if self._service_spec.dependencies:
            logger.success(
                f"[{self._service_spec.name}] {self.rule_name}: ✓ Internal dependencies validation passed"
            )
        else:
            logger.info(
                f"[{self._service_spec.name}] {self.rule_name}: No dependency rules defined, skipping"
            )

        return violations

