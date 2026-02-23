"""DSL rule: files_must_be_snake_case — .py filenames must use snake_case."""

from __future__ import annotations

from pathlib import Path

from pyarchrules.core.rules.base.fs_rule import FsBaseRule
from pyarchrules.core.rules.checks.fs import collect_files_recursive, is_snake_case_filename
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class FilesMustBeSnakeCaseRule(FsBaseRule):
    """Assert that all .py files within *folder* use ``snake_case`` naming.

    Files starting with an underscore (e.g. ``__init__.py``, ``_internal.py``) are skipped.

    DSL usage::

        rules.for_service("backend").files_must_be_snake_case("domain")
    """

    def __init__(self, service_spec: ServiceSpec, folder: str | None = None):
        super().__init__(service_spec, folder=folder)

    @property
    def rule_name(self) -> str:
        return "files_must_be_snake_case"

    def _check_directory(self, directory: Path) -> list[RuleViolation]:
        violations = []
        for f in collect_files_recursive(directory, "*.py"):
            stem = f.stem
            if stem.startswith("_"):
                continue  # skip __init__.py, _private.py etc.
            if not is_snake_case_filename(stem):
                rel = f.relative_to(self._service_spec.absolute_path)
                violations.append(
                    self._make_violation(
                        message=f"File '{rel}' is not snake_case",
                        details={"file": str(rel)},
                    )
                )
        return violations
