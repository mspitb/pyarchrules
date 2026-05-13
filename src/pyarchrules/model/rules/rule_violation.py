"""RuleViolation model — single architecture-rule violation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(slots=True, frozen=True)
class RuleViolation:
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
    file : str, optional
        Path of the offending source file (relative to project root when
        available). Promoted to a first-class field so SARIF / JSON / IDE
        integrations don't have to dig in ``details``.
    line : int, optional
        1-based line number inside *file*. ``None`` when the violation is
        not tied to a specific line.
    details : dict
        Optional extra context (e.g. cycle paths, conflicting rule names).
    """

    rule_name: str
    service_name: str
    message: str
    severity: Literal["error", "warning"] = "error"
    file: str | None = None
    line: int | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_log_message(self) -> str:
        """Format the violation as a single log line.

        Returns
        -------
        str
            ``[service] rule: message`` with optional ``file:line`` and
            ``details`` suffixes.
        """
        location = ""
        if self.file:
            location = f" ({self.file}{':' + str(self.line) if self.line else ''})"
        details = f" details={self.details}" if self.details else ""
        return f"[{self.service_name}] {self.rule_name}: {self.message}{location}{details}"
