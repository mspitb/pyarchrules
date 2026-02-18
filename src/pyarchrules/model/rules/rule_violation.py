from typing import Any, Literal

from pydantic import BaseModel, Field


class RuleViolation(BaseModel):
    rule_name: str
    service_name: str
    message: str
    severity: Literal["error", "warning"] = "error"
    details: dict[str, Any] = Field(default_factory=dict)

    def to_log_message(self) -> str:
        details = f" details={self.details}" if self.details else ""
        return f"[{self.service_name}] {self.rule_name}: {self.message}{details}"
