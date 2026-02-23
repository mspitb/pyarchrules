"""DSL rule: max_depth — directory nesting must not exceed N levels."""

from __future__ import annotations

from pathlib import Path

from pyarchrules.core.rules.base.fs_rule import FsBaseRule
from pyarchrules.core.rules.checks.fs import measure_depth
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class MaxDepthRule(FsBaseRule):
    """Assert that the directory tree does not exceed *max_depth* nesting levels.

    The service root (or *folder* when specified) counts as depth 0.

    DSL usage::

        rules.for_service("backend").max_depth(3)
        rules.for_service("backend").max_depth(2, folder="domain")
    """

    def __init__(self, service_spec: ServiceSpec, max_depth: int, folder: str | None = None):
        super().__init__(service_spec, folder=folder)
        self._max_depth = max_depth

    @property
    def rule_name(self) -> str:
        return "max_depth"

    def _check_directory(self, directory: Path) -> list[RuleViolation]:
        actual = measure_depth(directory)
        if actual <= self._max_depth:
            return []
        return [
            self._make_violation(
                message=f"Directory depth {actual} exceeds allowed maximum of {self._max_depth}",
                details={"actual_depth": actual, "max_depth": self._max_depth},
            )
        ]
