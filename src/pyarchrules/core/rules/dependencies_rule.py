"""Internal dependencies validation rule."""

from __future__ import annotations

from pathlib import Path

from pyarchrules.core.errors import ConfigError
from pyarchrules.core.rules.checks.imports import (
    STDLIB_MODULES,
    collect_imports,
    iter_py_files,
    resolve_relative,
)
from pyarchrules.core.rules.dsl import DslRule
from pyarchrules.core.rules.linter import LinterRule
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.dependency import DependencyRule
from pyarchrules.model.spec.project_spec import ProjectSpec
from pyarchrules.model.spec.service_spec import ServiceSpec


class DependenciesRule(LinterRule, DslRule):
    """Validate internal import directions within a service.

    Config example::

        dependencies = ["api -> domain", "domain -> infra"]

    ``source -> target`` means *source* may import from *target*. The rules form
    an allow-list: an import between different top-level folders is reported
    unless some rule permits it (same-package imports are always allowed).
    """

    name = "internal_dependencies"
    dsl_method = "dependencies"

    @classmethod
    def from_spec(
        cls, service_spec: ServiceSpec, project_spec: ProjectSpec
    ) -> DependenciesRule | None:
        return cls(service_spec) if service_spec.dependencies else None

    @classmethod
    def parse_rules(
        cls, raw_rules: list[str], *, service_name: str | None = None
    ) -> list[DependencyRule]:
        """Parse rule strings (syntax only).

        Raises
        ------
        ConfigError
            On malformed syntax, ``* -> *`` or invalid paths.
        """
        prefix = f"Service '{service_name}': " if service_name else ""
        parsed = []
        for raw in raw_rules:
            try:
                parsed.append(DependencyRule.parse(raw))
            except ConfigError as e:
                raise ConfigError(f"{prefix}invalid dependency rule '{raw}': {e}") from None
        return parsed

    @classmethod
    def detect_overlaps(
        cls, rules: list[DependencyRule]
    ) -> list[tuple[DependencyRule, DependencyRule]]:
        """Return ``(broader, narrower)`` pairs of overlapping rules.

        Two rules overlap when one source is an ancestor of the other's and
        their targets cover the same area. Wildcards never overlap.
        """
        overlaps = []
        for i, first in enumerate(rules):
            for second in rules[i + 1 :]:
                if "*" in (first.source, first.target, second.source, second.target):
                    continue
                if not _paths_overlap(first.target, second.target):
                    continue
                if _is_parent(first.source, second.source):
                    overlaps.append((first, second))
                elif _is_parent(second.source, first.source):
                    overlaps.append((second, first))
        return overlaps

    def _check(self) -> list[RuleViolation]:
        rules = self._service_spec.dependency_rules
        service_dir = self._service_spec.absolute_path

        violations = [
            self._violation(
                f"Overlapping dependency rules: '{broader.original}' is broader than "
                f"'{narrower.original}'; the broader rule subsumes the narrower one",
                severity="warning",
                details={"rules": [broader.original, narrower.original]},
            )
            for broader, narrower in self.detect_overlaps(rules)
        ]

        missing = self._missing_paths(service_dir, rules)
        if missing:
            return violations + missing
        return violations + self._check_imports(service_dir, rules)

    def _missing_paths(self, service_dir: Path, rules: list[DependencyRule]) -> list[RuleViolation]:
        """Every source/target top-level folder named by a rule must exist."""
        violations = []
        checked: set[str] = set()
        for rule in rules:
            for role, path in (("source", rule.source), ("target", rule.target)):
                if path == "*" or path in checked:
                    continue
                checked.add(path)
                if not (service_dir / path.split("/")[0]).is_dir():
                    violations.append(
                        self._violation(
                            f"Dependency rule references non-existent {role} "
                            f"package '{path}' in rule '{rule.original}'",
                            details={"rule": rule.original, "missing_path": path},
                        )
                    )
        return violations

    def _check_imports(self, service_dir: Path, rules: list[DependencyRule]) -> list[RuleViolation]:
        internal_packages = {
            d.name
            for d in service_dir.iterdir()
            if d.is_dir() and not d.name.startswith((".", "_"))
        }
        root_name = service_dir.name

        violations: list[RuleViolation] = []
        for py_file in iter_py_files(service_dir):
            rel_path = py_file.relative_to(service_dir)
            module_path = rel_path.parent.as_posix()
            # Files at the service root belong to no package; rules don't apply.
            if module_path == ".":
                continue

            for imp in collect_imports(py_file):
                if not imp.module:
                    continue
                if not imp.is_relative and imp.module.split(".", 1)[0] in STDLIB_MODULES:
                    continue

                imported = self._resolve_import(
                    imp.module, module_path, root_name, internal_packages
                )
                # Third-party imports have no matching folder inside the service.
                if imported.split("/")[0] not in internal_packages:
                    continue

                if not self._is_import_allowed(module_path, imported, rules):
                    violations.append(
                        self._violation(
                            f"Forbidden import in {rel_path}: '{imp.module}'",
                            file=str(rel_path),
                            line=imp.lineno or None,
                            details={
                                "from_module": module_path,
                                "imported": imported,
                                "import_statement": imp.module,
                            },
                        )
                    )

        violations.sort(key=lambda v: (v.file or "", v.line or 0, v.message))
        return violations

    @staticmethod
    def _resolve_import(
        imp: str, current_module: str, root_name: str, internal_packages: set[str]
    ) -> str:
        """Resolve an import string to a service-relative folder path.

        ``"domain.models"`` → ``"domain/models"``; ``"..utils"`` imported from
        ``"api/controllers"`` → ``"api/utils"``. An absolute import prefixed with
        the service directory name (``"core.legacy.x"`` in service ``core``) is
        resolved without that prefix, unless the service has a folder of that name.
        """
        if not imp.startswith("."):
            resolved_path = imp.replace(".", "/")
            head, _, tail = resolved_path.partition("/")
            if head == root_name and head not in internal_packages and tail:
                return tail
            return resolved_path

        resolved = resolve_relative(imp, [p for p in current_module.split("/") if p])
        return "/".join(resolved) if resolved is not None else ""

    @staticmethod
    def _is_import_allowed(from_module: str, to_module: str, rules: list[DependencyRule]) -> bool:
        """Whether code in *from_module* may import *to_module*.

        Same-package imports are always allowed. Otherwise some rule must have a
        matching source (or ``*``) and a matching target (or ``*``).
        """
        if from_module.split("/")[0] == to_module.split("/")[0]:
            return True

        return any(
            (rule.source == "*" or _is_within(from_module, rule.source))
            and (rule.target == "*" or _is_within(to_module, rule.target))
            for rule in rules
        )


def _is_within(path: str, folder: str) -> bool:
    return path == folder or path.startswith(folder + "/")


def _is_parent(parent: str, child: str) -> bool:
    return parent != child and child.startswith(parent + "/")


def _paths_overlap(first: str, second: str) -> bool:
    return first == second or _is_parent(first, second) or _is_parent(second, first)
