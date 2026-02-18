from pydantic import BaseModel, Field

from pyarchrules.model.rules.rule_violation import RuleViolation


class RuleEvalResult(BaseModel):
    violations: list[RuleViolation] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.violations) == 0

    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "warning")
