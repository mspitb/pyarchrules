"""RuleEvalResult — aggregated outcome of a validation run."""

from __future__ import annotations

from dataclasses import dataclass, field

from pyarchrules.model.rules.rule_violation import RuleViolation


@dataclass(slots=True, frozen=True)
class RuleEvalResult:
    """Aggregated result of running one or more rules.

    Attributes
    ----------
    violations : list[RuleViolation]
        All violations collected during the validation run.
    """

    violations: list[RuleViolation] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return ``True`` when no violations were found."""
        return len(self.violations) == 0

    @property
    def error_count(self) -> int:
        """Number of error-severity violations."""
        return sum(1 for v in self.violations if v.severity == "error")

    @property
    def warning_count(self) -> int:
        """Number of warning-severity violations."""
        return sum(1 for v in self.violations if v.severity == "warning")
