"""Tree structure validation rule."""

from pathlib import Path

from loguru import logger

from pyarchrules.core.rules.rule import Rule
from pyarchrules.model.rules.rule_violation import RuleViolation


class TreeRule(Rule):
    """Validates directory tree structure.

    Config example:
        tree = ["api", "api/model", "domain"]
        tree_strict = true
        tree_allow_files = true
    """

    @property
    def rule_name(self) -> str:
        return "tree_structure"

    def validate(self) -> list[RuleViolation]:
        if not self._service_spec.tree:
            logger.info(f"[{self._service_spec.name}] {self.rule_name}: No tree config, skipping")
            return []

        service_dir = self._service_spec.absolute_path

        if not service_dir.exists():
            return [
                RuleViolation(
                    rule_name=self.rule_name,
                    service_name=self._service_spec.name,
                    severity="error",
                    message=f"Service directory does not exist: {self._service_spec.path}",
                )
            ]

        violations = []

        missing_paths = [p for p in self._service_spec.tree if not (service_dir / p).exists()]
        if missing_paths:
            violations.append(
                RuleViolation(
                    rule_name=self.rule_name,
                    service_name=self._service_spec.name,
                    severity="error",
                    message=f"Missing required paths: {missing_paths}",
                    details={"missing_paths": missing_paths},
                )
            )

        if self._service_spec.tree_strict:
            violations.extend(self._check_strict_mode(service_dir))

        if not violations:
            strict_msg = " (strict mode)" if self._service_spec.tree_strict else ""
            logger.success(
                f"[{self._service_spec.name}] {self.rule_name}: "
                f"✓ {len(self._service_spec.tree)} path(s){strict_msg}"
            )

        return violations

    def _check_strict_mode(self, service_dir: Path) -> list[RuleViolation]:
        violations = []

        for tree_path in self._service_spec.tree:
            full_path = service_dir / tree_path
            if not full_path.is_dir():
                continue

            actual_items = {
                item.name for item in full_path.iterdir() if not item.name.startswith((".", "__"))
            }

            expected_subdirs = self._get_expected_subdirs(tree_path)
            extra_items = actual_items - expected_subdirs

            if self._service_spec.tree_allow_files and extra_items:
                extra_items = {item for item in extra_items if (full_path / item).is_dir()}

            if extra_items:
                msg_suffix = " (only folders)" if self._service_spec.tree_allow_files else ""
                violations.append(
                    RuleViolation(
                        rule_name=self.rule_name,
                        service_name=self._service_spec.name,
                        severity="warning",
                        message=f"Extra items in '{tree_path}' (tree_strict=true{msg_suffix}): "
                        f"{sorted(extra_items)}",
                        details={
                            "path": tree_path,
                            "extra_items": sorted(extra_items),
                            "expected": sorted(expected_subdirs),
                            "allow_files": self._service_spec.tree_allow_files,
                        },
                    )
                )

        return violations

    def _get_expected_subdirs(self, tree_path: str) -> set[str]:
        expected_subdirs = set()
        path_prefix = tree_path.rstrip("/") + "/"

        for other_path in self._service_spec.tree:
            if other_path.startswith(path_prefix):
                rest = other_path[len(path_prefix) :]
                subdir = rest.split("/")[0] if "/" in rest else rest
                if subdir:
                    expected_subdirs.add(subdir)

        return expected_subdirs
