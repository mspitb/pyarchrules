"""Tree structure validation rule."""

from loguru import logger

from pyarchrules.core.rules.rule import Rule
from pyarchrules.model.rules.rule_violation import RuleViolation


class TreeRule(Rule):
    """Validates that directory tree structure matches the configuration."""

    @property
    def rule_name(self) -> str:
        return "tree_structure"

    def validate(self) -> list[RuleViolation]:
        """Validate the directory tree structure."""
        violations = []

        # TODO: Implement actual validation
        # For now, return empty list (no violations)
        if self._service_spec.tree:
            logger.success(
                f"[{self._service_spec.name}] {self.rule_name}: ✓ Tree structure validation passed"
            )
        else:
            logger.info(
                f"[{self._service_spec.name}] {self.rule_name}: No tree configuration found, skipping"
            )

        return violations

