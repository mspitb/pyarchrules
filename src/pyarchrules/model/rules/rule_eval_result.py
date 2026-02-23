from pydantic import BaseModel, Field

from pyarchrules.model.rules.rule_violation import RuleViolation


class RuleEvalResult(BaseModel):
    """Aggregated result of running one or more rules.

    Attributes
    ----------
    violations : list[RuleViolation]
        All violations collected during the validation run.
    """

    violations: list[RuleViolation] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Return ``True`` when no violations were found.

        Returns
        -------
        bool
        """
        return len(self.violations) == 0

    @property
    def error_count(self) -> int:
        """Number of error-severity violations.

        Returns
        -------
        int
        """
        return sum(1 for v in self.violations if v.severity == "error")

    @property
    def warning_count(self) -> int:
        """Number of warning-severity violations.

        Returns
        -------
        int
        """
        return sum(1 for v in self.violations if v.severity == "warning")
