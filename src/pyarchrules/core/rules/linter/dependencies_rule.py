"""Internal dependencies validation rule."""

import ast
from pathlib import Path

from loguru import logger

from pyarchrules.core.errors import PyArchError
from pyarchrules.core.rules.rule import Rule
from pyarchrules.model.rules.rule_violation import RuleViolation

STDLIB_MODULES = frozenset(
    {
        "os",
        "sys",
        "re",
        "pathlib",
        "typing",
        "collections",
        "ast",
        "json",
        "datetime",
        "time",
        "itertools",
        "functools",
        "contextlib",
        "io",
    }
)


class DependenciesRule(Rule):
    """Validates internal module dependencies within a service.

    Config example:
        dependencies = ["api -> domain", "domain -> infra"]

    Rules:
    - Only -> arrows allowed (source -> target means source can use target)
    - No overlapping rules
    - Only validates configured dependencies (unconfigured imports allowed)
    """

    @property
    def rule_name(self) -> str:
        return "internal_dependencies"

    def validate(self) -> list[RuleViolation]:
        if not self._service_spec.dependencies:
            logger.info(
                f"[{self._service_spec.name}] {self.rule_name}: No dependency rules, skipping"
            )
            return []

        violations = []
        dependency_rules = []

        for dep in self._service_spec.dependencies:
            try:
                dependency_rules.append(self._parse_dependency_rule(dep))
            except PyArchError as e:
                violations.append(
                    RuleViolation(
                        rule_name=self.rule_name,
                        service_name=self._service_spec.name,
                        severity="error",
                        message=f"Invalid dependency rule: {dep}",
                        details={"rule": dep, "error": str(e)},
                    )
                )

        if violations:
            return violations

        violations.extend(self._check_overlapping_rules(dependency_rules))
        if violations:
            return violations

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

        violations.extend(self._check_imports(service_dir, dependency_rules))

        if not violations:
            logger.success(
                f"[{self._service_spec.name}] {self.rule_name}: "
                f"✓ {len(dependency_rules)} rule(s) validated"
            )

        return violations

    def _parse_dependency_rule(self, rule: str) -> dict:
        rule = rule.strip()

        if "<-" in rule:
            raise PyArchError(
                "Invalid arrow '<-'. Use '->' (e.g., 'api -> domain' means api can use domain)"
            )

        if "->" not in rule:
            raise PyArchError("Missing '->'. Example: 'api -> domain' means api can use domain")

        parts = rule.split("->", 1)
        source, target = parts[0].strip(), parts[1].strip()

        if not source or not target:
            raise PyArchError("Empty source or target")

        for path in (source, target):
            if path.startswith(("/", "\\")) or ".." in path:
                raise PyArchError(f"Invalid path: {path}")

        return {"from": source, "to": target, "original": rule}

    def _check_overlapping_rules(self, rules: list[dict]) -> list[RuleViolation]:
        violations = []

        for i, rule1 in enumerate(rules):
            for rule2 in rules[i + 1 :]:
                src1, src2 = rule1["from"], rule2["from"]
                tgt1, tgt2 = rule1["to"], rule2["to"]

                if self._is_parent_path(src1, src2) or self._is_parent_path(src2, src1):
                    if self._paths_overlap(tgt1, tgt2):
                        violations.append(
                            RuleViolation(
                                rule_name=self.rule_name,
                                service_name=self._service_spec.name,
                                severity="error",
                                message=f"Overlapping rules: "
                                f"'{rule1['original']}' and '{rule2['original']}'",
                                details={
                                    "rule1": rule1["original"],
                                    "rule2": rule2["original"],
                                },
                            )
                        )

        return violations

    @staticmethod
    def _is_parent_path(parent: str, child: str) -> bool:
        return parent != child and (
            child.startswith(parent + "/") or child.startswith(parent + "\\")
        )

    @staticmethod
    def _paths_overlap(path1: str, path2: str) -> bool:
        return (
            path1 == path2
            or DependenciesRule._is_parent_path(path1, path2)
            or DependenciesRule._is_parent_path(path2, path1)
        )

    def _check_imports(self, service_dir: Path, rules: list[dict]) -> list[RuleViolation]:
        allowed_deps = {}
        for rule in rules:
            allowed_deps.setdefault(rule["from"], []).append(rule["to"])

        violations = []

        for py_file in service_dir.rglob("*.py"):
            if "__pycache__" in py_file.parts:
                continue

            try:
                rel_path = py_file.relative_to(service_dir)
                module_path = str(rel_path.parent).replace("\\", "/")
                if module_path == ".":
                    module_path = ""
            except ValueError:
                continue

            try:
                imports = self._extract_imports(py_file)
            except Exception as e:
                logger.warning(f"Failed to parse {py_file.name}: {e}")
                continue

            for imp in imports:
                if not self._is_internal_import(imp):
                    continue

                imported_module = self._resolve_import(imp, module_path)

                if not self._is_import_allowed(module_path, imported_module, allowed_deps):
                    violations.append(
                        RuleViolation(
                            rule_name=self.rule_name,
                            service_name=self._service_spec.name,
                            severity="error",
                            message=f"Forbidden import in {rel_path}: {imp}",
                            details={
                                "file": str(rel_path),
                                "from_module": module_path or "(root)",
                                "imported": imported_module,
                                "import_statement": imp,
                            },
                        )
                    )

        return violations

    @staticmethod
    def _extract_imports(py_file: Path) -> list[str]:
        imports = []

        try:
            with open(py_file, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(py_file))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
        except SyntaxError:
            pass

        return imports

    @staticmethod
    def _is_internal_import(imp: str) -> bool:
        if imp.startswith("."):
            return True

        first_part = imp.split(".", 1)[0]
        return first_part not in STDLIB_MODULES

    @staticmethod
    def _resolve_import(imp: str, current_module: str) -> str:
        if not imp.startswith("."):
            return imp.split(".", 1)[0]

        parts = current_module.split("/") if current_module else []
        dots = len(imp) - len(imp.lstrip("."))

        for _ in range(dots - 1):
            if parts:
                parts.pop()

        rest = imp[dots:]
        if rest:
            parts.append(rest)

        return "/".join(parts)

    @staticmethod
    def _is_import_allowed(from_module: str, to_module: str, allowed_deps: dict) -> bool:
        for source, targets in allowed_deps.items():
            if from_module == source or from_module.startswith(source + "/"):
                for target in targets:
                    if to_module == target or to_module.startswith(target + "/"):
                        return True

        return True
