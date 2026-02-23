"""DSL rule: no_test_files_in — no test files allowed in production folders."""

from __future__ import annotations

from pathlib import Path

from pyarchrules.core.rules.base.fs_rule import FsBaseRule
from pyarchrules.core.rules.checks.fs import collect_files_recursive
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class NoTestFilesInRule(FsBaseRule):
    """Assert that no test files (``test_*.py`` / ``*_test.py``) exist inside *folder*.

    DSL usage::

        rules.for_service("backend").no_test_files_in("domain")
        rules.for_service("backend").no_test_files_in("api")
    """

    def __init__(self, service_spec: ServiceSpec, folder: str):
        super().__init__(service_spec, folder=folder)

    @property
    def rule_name(self) -> str:
        return "no_test_files_in"

    def _check_directory(self, directory: Path) -> list[RuleViolation]:
        violations = []
        for f in collect_files_recursive(directory, "*.py"):
            name = f.name
            if name.startswith("test_") or name.endswith("_test.py"):
                rel = f.relative_to(self._service_spec.absolute_path)
                violations.append(
                    self._make_violation(
                        message=f"Test file found in production folder: '{rel}'",
                        details={"file": str(rel)},
                    )
                )
        return violations
