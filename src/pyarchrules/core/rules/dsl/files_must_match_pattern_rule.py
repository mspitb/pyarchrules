"""DSL rule: files_must_match_pattern — all files in a folder match a glob pattern."""

from __future__ import annotations

import fnmatch
from pathlib import Path

from pyarchrules.core.rules.base.fs_rule import FsBaseRule
from pyarchrules.core.rules.checks.fs import collect_files
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class FilesMustMatchPatternRule(FsBaseRule):
    """Assert that every file directly inside *folder* matches *pattern*.

    DSL usage::

        rules.for_service("backend").files_must_match_pattern("tests", "test_*.py")
    """

    def __init__(self, service_spec: ServiceSpec, folder: str, pattern: str):
        super().__init__(service_spec, folder=folder)
        self._pattern = pattern

    @property
    def rule_name(self) -> str:
        return "files_must_match_pattern"

    def _check_directory(self, directory: Path) -> list[RuleViolation]:
        all_files = collect_files(directory)
        violations = []
        for f in all_files:
            if not fnmatch.fnmatch(f.name, self._pattern):
                violations.append(
                    self._make_violation(
                        message=f"File '{f.name}' does not match pattern '{self._pattern}'",
                        details={"file": str(f.name), "pattern": self._pattern},
                    )
                )
        return violations
