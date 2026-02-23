"""Tree structure validation rule."""

from __future__ import annotations

from pyarchrules.core.rules.rule import Rule
from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class TreeStructureRule(Rule):
    """Rule that validates directory tree structure against specification."""

    def __init__(self, service_spec: ServiceSpec):
        super().__init__(service_spec)

    def validate(self) -> list[RuleViolation]:
        """Validate the directory structure against the tree specification."""
        violations = []
        service_dir = self._service_spec.absolute_path

        if not service_dir.exists():
            violations.append(
                RuleViolation(
                    rule_name=self.rule_name,
                    service_name=self._service_spec.name,
                    severity="error",
                    message=f"Service directory '{service_dir}' does not exist.",
                )
            )
            return violations

        tree = self._service_spec.tree
        if not tree:
            # No tree specification, nothing to validate
            return violations

        for path, node_spec in tree.items():
            violations.extend(self._validate_node(service_dir, path, node_spec))

        return violations

    def _validate_node(self, service_dir, path: str, node_spec) -> list[RuleViolation]:
        """Validate a single node in the tree structure."""
        violations = []
        target_dir = service_dir / path

        if not target_dir.exists():
            violations.append(
                RuleViolation(
                    rule_name=self.rule_name,
                    service_name=self._service_spec.name,
                    severity="error",
                    message=f"Required directory '{path}' does not exist.",
                    details={"path": path},
                )
            )
            return violations

        if not target_dir.is_dir():
            violations.append(
                RuleViolation(
                    rule_name=self.rule_name,
                    service_name=self._service_spec.name,
                    severity="error",
                    message=f"Path '{path}' exists but is not a directory.",
                    details={"path": path},
                )
            )
            return violations

        # Check required subdirectories
        existing_dirs = {
            d.name for d in target_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
        }
        required_dirs = set(node_spec.subdirs)
        missing_dirs = required_dirs - existing_dirs

        if missing_dirs:
            violations.append(
                RuleViolation(
                    rule_name=self.rule_name,
                    service_name=self._service_spec.name,
                    severity="error",
                    message=f"Missing required subdirectories in '{path}': {sorted(missing_dirs)}",
                    details={"path": path, "missing": sorted(missing_dirs)},
                )
            )

        # Check for extra directories if not allowed
        if not node_spec.allow_extra:
            extra_dirs = existing_dirs - required_dirs
            if extra_dirs:
                violations.append(
                    RuleViolation(
                        rule_name=self.rule_name,
                        service_name=self._service_spec.name,
                        severity="warning",
                        message=f"Extra directories not allowed in '{path}': {sorted(extra_dirs)}",
                        details={"path": path, "extra": sorted(extra_dirs)},
                    )
                )

        return violations

    @property
    def rule_name(self) -> str:
        return "tree_structure"
