"""Internal dependencies validation rule."""

import ast
from pathlib import Path

from loguru import logger

from pyarchrules.core.errors import PyArchError
from pyarchrules.core.rules.checks.imports import STDLIB_MODULES
from pyarchrules.core.rules.rule import Rule
from pyarchrules.model.rules.rule_violation import RuleViolation


class DependenciesRule(Rule):
    """Validates internal module dependencies within a service.

    Config example::

        dependencies = ["api -> domain", "domain -> infra"]

    ``source -> target`` means *source* is allowed to import from *target*.
    Modules whose source folder is **not** covered by any rule are unrestricted.
    Modules whose source folder **is** covered may only import from the listed targets.

    Parameters
    ----------
    service_spec : ServiceSpec
        Specification of the service being validated.
    """

    @property
    def rule_name(self) -> str:
        return "internal_dependencies"

    def validate(self) -> list[RuleViolation]:
        """Run all configured dependency rules against the service.

        Returns
        -------
        list[RuleViolation]
        """
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

        violations.extend(self._validate_rule_paths(service_dir, dependency_rules))
        if violations:
            return violations

        violations.extend(self._check_imports(service_dir, dependency_rules))

        if not violations:
            logger.success(
                f"[{self._service_spec.name}] {self.rule_name}: "
                f"✓ {len(dependency_rules)} rule(s) validated"
            )

        return violations

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

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

        if source == "*" and target == "*":
            raise PyArchError("'* -> *' is not allowed — it would permit everything")

        for path in (source, target):
            if path == "*":
                continue
            if path.startswith(("/", "\\")) or ".." in path:
                raise PyArchError(f"Invalid path: {path}")

        return {"from": source, "to": target, "original": rule}

    # ------------------------------------------------------------------
    # Overlap check
    # ------------------------------------------------------------------

    def _check_overlapping_rules(self, rules: list[dict]) -> list[RuleViolation]:
        violations = []

        for i, rule1 in enumerate(rules):
            for rule2 in rules[i + 1 :]:
                src1, src2 = rule1["from"], rule2["from"]
                tgt1, tgt2 = rule1["to"], rule2["to"]

                # Wildcard rules never overlap with specific rules
                if "*" in (src1, src2, tgt1, tgt2):
                    continue

                if self._is_parent_path(src1, src2) or self._is_parent_path(src2, src1):
                    if self._paths_overlap(tgt1, tgt2):
                        violations.append(
                            RuleViolation(
                                rule_name=self.rule_name,
                                service_name=self._service_spec.name,
                                severity="error",
                                message=(
                                    f"Overlapping rules: "
                                    f"'{rule1['original']}' and '{rule2['original']}'"
                                ),
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

    # ------------------------------------------------------------------
    # Import scanning
    # ------------------------------------------------------------------

    def _validate_rule_paths(self, service_dir: Path, rules: list[dict]) -> list[RuleViolation]:
        """Check that every source and target folder referenced in a rule actually exists.

        Parameters
        ----------
        service_dir : Path
            Absolute path to the service root.
        rules : list[dict]
            Parsed dependency rules.

        Returns
        -------
        list[RuleViolation]
        """
        violations = []
        checked: set[str] = set()

        for rule in rules:
            for role, path in (("source", rule["from"]), ("target", rule["to"])):
                if path == "*" or path in checked:
                    continue
                checked.add(path)
                # Only validate the top-level folder — nested paths like
                # "domain/models" may not exist as dirs when the rule is broad.
                top_level = path.split("/")[0]
                if not (service_dir / top_level).is_dir():
                    violations.append(
                        RuleViolation(
                            rule_name=self.rule_name,
                            service_name=self._service_spec.name,
                            severity="error",
                            message=(
                                f"Dependency rule references non-existent {role} "
                                f"package '{path}' in rule '{rule['original']}'"
                            ),
                            details={"rule": rule["original"], "missing_path": path},
                        )
                    )

        return violations

    def _check_imports(self, service_dir: Path, rules: list[dict]) -> list[RuleViolation]:
        # Build source → [allowed targets] map
        allowed_deps: dict[str, list[str]] = {}
        for rule in rules:
            allowed_deps.setdefault(rule["from"], []).append(rule["to"])

        # Discover internal packages: top-level directories inside the service
        internal_packages = {
            d.name
            for d in service_dir.iterdir()
            if d.is_dir() and not d.name.startswith((".", "_"))
        }

        violations = []

        for py_file in sorted(service_dir.rglob("*.py")):
            if "__pycache__" in py_file.parts:
                continue

            try:
                rel_path = py_file.relative_to(service_dir)
                module_path = str(rel_path.parent).replace("\\", "/")
                if module_path == ".":
                    module_path = ""
            except ValueError:
                continue

            # Files at the service root (main.py, __init__.py, etc.) are not
            # inside any named package — dependency rules don't apply to them.
            if not module_path:
                continue

            try:
                imports = self._extract_imports(py_file)
            except Exception as e:
                logger.warning(f"Failed to parse {py_file.name}: {e}")
                continue

            for imp in imports:
                # Skip stdlib
                if not self._is_internal_import(imp):
                    continue

                imported_module = self._resolve_import(imp, module_path)

                # Skip third-party libs — only check imports whose root folder
                # actually exists inside the service directory
                top_level = imported_module.split("/")[0]
                if top_level not in internal_packages:
                    continue

                if not self._is_import_allowed(module_path, imported_module, allowed_deps):
                    violations.append(
                        RuleViolation(
                            rule_name=self.rule_name,
                            service_name=self._service_spec.name,
                            severity="error",
                            message=f"Forbidden import in {rel_path}: '{imp}'",
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
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
        except SyntaxError as e:
            logger.warning(f"Failed to parse {py_file.name}: {e}")
        return imports

    @staticmethod
    def _is_internal_import(imp: str) -> bool:
        if imp.startswith("."):
            return True
        first_part = imp.split(".", 1)[0]
        return first_part not in STDLIB_MODULES

    @staticmethod
    def _resolve_import(imp: str, current_module: str) -> str:
        """Resolve an import string to a service-relative folder path.

        Parameters
        ----------
        imp : str
            Raw import string, e.g. ``"domain.models"`` or ``"..utils"``.
        current_module : str
            The ``/``-separated folder of the file being analysed, e.g. ``"api/controllers"``.

        Returns
        -------
        str
            Service-relative path, e.g. ``"domain/models"``.
        """
        if not imp.startswith("."):
            # Absolute import — convert dots to slashes to get the full path
            return imp.replace(".", "/")

        parts = current_module.split("/") if current_module else []
        dots = len(imp) - len(imp.lstrip("."))

        for _ in range(dots - 1):
            if parts:
                parts.pop()

        rest = imp[dots:]
        if rest:
            parts.append(rest.replace(".", "/"))

        return "/".join(parts)

    @staticmethod
    def _is_import_allowed(from_module: str, to_module: str, allowed_deps: dict) -> bool:
        """Return ``True`` if importing *to_module* from *from_module* is permitted.

        Rules:
        - Same-package imports are always allowed.
        - ``* -> target`` — any source may import *target*.
        - ``source -> *`` — *source* may import anything.
        - ``source -> target`` — explicit pair.
        - Anything else is forbidden.

        Parameters
        ----------
        from_module : str
            The ``/``-separated folder of the importing file, e.g. ``"api/controllers"``.
        to_module : str
            The resolved target package path, e.g. ``"domain/models"``.
        allowed_deps : dict
            Mapping of source → list of allowed targets, built from the configured rules.

        Returns
        -------
        bool
        """
        # Same-package imports are always allowed (e.g. api/a importing api/b)
        from_top = from_module.split("/")[0] if from_module else ""
        to_top = to_module.split("/")[0] if to_module else ""
        if from_top and from_top == to_top:
            return True

        # Check explicit rules — wildcard sources/targets handled here too
        for source, targets in allowed_deps.items():
            # Does the source side match?
            if source == "*":
                source_matches = True
            else:
                source_matches = from_module == source or from_module.startswith(source + "/")

            if not source_matches:
                continue

            for target in targets:
                # source -> * means source may import anything
                if target == "*":
                    return True
                if to_module == target or to_module.startswith(target + "/"):
                    return True

        # Source uncovered or covered but no target matched — forbidden
        return False
