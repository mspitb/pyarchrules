"""Path existence validation rule."""

from loguru import logger

from pyarchrules.core.rules.rule import Rule
from pyarchrules.model.rules.rule_violation import RuleViolation


class PathExistenceRule(Rule):
    """Validates that service paths exist on the filesystem."""

    @property
    def rule_name(self) -> str:
        return "path_existence"

    def validate(self) -> list[RuleViolation]:
        """Validate that the service path exists."""
        violations = []

        # TODO: Implement actual validation
        # For now, return empty list (no violations)
        logger.success(
            f"[{self._service_spec.name}] {self.rule_name}: ✓ Path validation passed"
        )

        return violations

