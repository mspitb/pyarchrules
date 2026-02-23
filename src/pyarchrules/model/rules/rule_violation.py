from typing import Any, Literal

from pydantic import BaseModel, Field


class RuleViolation(BaseModel):
    """A single rule violation produced by a failed architecture check.

    Attributes
    ----------
    rule_name : str
        Identifier of the rule that produced this violation.
    service_name : str
        Name of the service the violation belongs to.
    message : str
        Human-readable description of the violation.
    severity : {"error", "warning"}
        ``"error"`` blocks the build; ``"warning"`` is informational only.
    details : dict
        Optional extra context (e.g. offending file paths, line numbers).
    """

    rule_name: str
    service_name: str
    message: str
    severity: Literal["error", "warning"] = "error"
    details: dict[str, Any] = Field(default_factory=dict)

    def to_log_message(self) -> str:
        """Format the violation as a single log line.

        Returns
        -------
        str
            ``[service_name] rule_name: message`` with optional ``details`` suffix.
        """
        details = f" details={self.details}" if self.details else ""
        return f"[{self.service_name}] {self.rule_name}: {self.message}{details}"
