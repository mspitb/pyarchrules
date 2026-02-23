"""DSL rule: must_contain_files — assert required files exist in the service root."""

from __future__ import annotations

from pathlib import Path

from pyarchrules.core.rules.base.fs_rule import FsBaseRule
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class MustContainFilesRule(FsBaseRule):
    """Assert that the service directory contains specific files.

    DSL usage::

        rules.for_service("backend").must_contain_files(["README.md", "pyproject.toml"])
    """

    def __init__(self, service_spec: ServiceSpec, files: list[str]):
        super().__init__(service_spec, folder=None)
        self._files = files

    @property
    def rule_name(self) -> str:
        return "must_contain_files"

    def _check_directory(self, directory: Path) -> list[RuleViolation]:
        missing = sorted(f for f in self._files if not (directory / f).exists())
        if not missing:
            return []
        return [
            self._make_violation(
                message=f"Missing required files: {missing}",
                details={"missing": missing},
            )
        ]
