"""DSL rule: classes_must_match_pattern — class names must conform to a regexp."""

from __future__ import annotations

from pathlib import Path

from pyarchrules.core.rules.base.import_rule import ImportBaseRule
from pyarchrules.core.rules.checks.imports import ImportInfo
from pyarchrules.core.rules.checks.naming import collect_class_names, matches_pattern
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class ClassesMustMatchPatternRule(ImportBaseRule):
    """Assert that every class defined in *folder* matches a regular expression.

    DSL usage::

        rules.for_service("backend").classes_must_match_pattern("domain/services", r".*Service$")
        rules.for_service("backend").classes_must_match_pattern("domain/repos", r".*Repository$")
    """

    def __init__(self, service_spec: ServiceSpec, folder: str, pattern: str):
        super().__init__(service_spec, folder=folder)
        self._pattern = pattern

    @property
    def rule_name(self) -> str:
        return "classes_must_match_pattern"

    def _check_file(
        self,
        file: Path,
        rel_path: Path,
        imports: list[ImportInfo],
    ) -> list[RuleViolation]:
        violations = []
        for class_name in collect_class_names(file):
            if not matches_pattern(class_name, self._pattern):
                violations.append(
                    self._make_violation(
                        rel_path=rel_path,
                        message=f"Class '{class_name}' does not match pattern '{self._pattern}'",
                        details={"class": class_name, "pattern": self._pattern},
                    )
                )
        return violations
