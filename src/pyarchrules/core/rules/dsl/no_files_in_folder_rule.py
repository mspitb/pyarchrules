"""DSL rule: no_files_in_folder — a folder must contain only subdirectories."""

from __future__ import annotations

from pathlib import Path

from pyarchrules.core.rules.base.fs_rule import FsBaseRule
from pyarchrules.core.rules.checks.fs import has_only_subdirs
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class NoFilesInFolderRule(FsBaseRule):
    """Assert that *folder* contains only subdirectories — no direct files.

    DSL usage::

        rules.for_service("backend").no_files_in_folder("domain")
    """

    def __init__(self, service_spec: ServiceSpec, folder: str):
        super().__init__(service_spec, folder=folder)

    @property
    def rule_name(self) -> str:
        return "no_files_in_folder"

    def _check_directory(self, directory: Path) -> list[RuleViolation]:
        ok, offending = has_only_subdirs(directory)
        if ok:
            return []
        names = sorted(f.name for f in offending)
        return [
            self._make_violation(
                message=f"Folder must not contain files directly: {names}",
                details={"files": names},
            )
        ]
