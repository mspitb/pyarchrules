"""Internal dependencies validation rule."""

from pathlib import Path
from typing import ClassVar

from pyarchrules.core.errors import ConfigError
from pyarchrules.core.rules.checks.imports import (
    STDLIB_MODULES,
    _resolve_relative,
    collect_imports,
    iter_py_files,
)
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

    CONFIG_KEYS: ClassVar[frozenset[str]] = frozenset({"dependencies"})

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
            return []

        # ``SpecLoader`` validates syntax at load time and raises
        # :class:`ConfigError` on malformed input.  We re-parse here so
        # programmatic construction (unit tests bypassing the loader) still
        # works for valid input. Overlaps are reported as warnings below.
        dependency_rules = self.parse_rules(
            self._service_spec.dependencies, service_name=self._service_spec.name
        )

        violations: list[RuleViolation] = []

        # Overlap detection — warning severity. The broader rule subsumes the
        # narrower one; the user can either delete the narrower rule or
        # replace the broader rule with the explicit set they meant.
        for r1, r2 in self.detect_overlaps(dependency_rules):
            violations.append(
                RuleViolation(
                    rule_name=self.rule_name,
                    service_name=self._service_spec.name,
                    severity="warning",
                    message=(
                        f"Overlapping dependency rules: '{r1['original']}' "
                        f"is broader than '{r2['original']}'; "
                        "the broader rule subsumes the narrower one"
                    ),
                    details={"rules": [r1["original"], r2["original"]]},
                )
            )

        service_dir = self._service_spec.absolute_path
        if not service_dir.exists():
            violations.append(
                RuleViolation(
                    rule_name=self.rule_name,
                    service_name=self._service_spec.name,
                    severity="error",
                    message=f"Service directory does not exist: {self._service_spec.path}",
                )
            )
            return violations

        path_violations = self._validate_rule_paths(service_dir, dependency_rules)
        if path_violations:
            violations.extend(path_violations)
            return violations

        violations.extend(self._check_imports(service_dir, dependency_rules))
        return violations

    # ------------------------------------------------------------------
    # Parsing  (load-time — raises ConfigError, never RuleViolation)
    # ------------------------------------------------------------------

    @classmethod
    def parse_rules(cls, raw_rules: list[str], *, service_name: str | None = None) -> list[dict]:
        """Parse dependency strings — syntax check only.

        Overlap detection is *not* part of this method (it was historically,
        but raising on overlap turned out to be too aggressive — a user
        writing ``"api -> domain"`` + ``"api/v1 -> domain"`` likely meant a
        narrowing, not a syntax error). Overlap is now reported as a
        warning-severity :class:`RuleViolation` at ``validate`` time via
        :meth:`detect_overlaps`.

        Parameters
        ----------
        raw_rules : list[str]
            Strings like ``"api -> domain"``.
        service_name : str, optional
            Used purely to enrich error messages.

        Returns
        -------
        list[dict]
            Parsed rules in the form ``{"from", "to", "original"}``.

        Raises
        ------
        ConfigError
            On malformed syntax, ``* -> *``, or invalid paths.
        """
        prefix = f"Service '{service_name}': " if service_name else ""
        parsed: list[dict] = []
        for raw in raw_rules:
            try:
                parsed.append(cls._parse_dependency_rule(raw))
            except ConfigError as e:
                raise ConfigError(f"{prefix}invalid dependency rule '{raw}': {e}") from None
        return parsed

    @classmethod
    def detect_overlaps(cls, parsed_rules: list[dict]) -> list[tuple[dict, dict]]:
        """Return pairs of overlapping rules (broader, narrower).

        Parameters
        ----------
        parsed_rules : list[dict]
            Output of :meth:`parse_rules`.

        Returns
        -------
        list[tuple[dict, dict]]
            Each tuple is ``(broader_rule, narrower_rule)`` — the first rule's
            source path is an ancestor of the second's, and both targets
            cover the same area.
        """
        overlaps: list[tuple[dict, dict]] = []
        for i, rule1 in enumerate(parsed_rules):
            for rule2 in parsed_rules[i + 1 :]:
                broader = cls._broader_of(rule1, rule2)
                if broader is None:
                    continue
                narrower = rule2 if broader is rule1 else rule1
                overlaps.append((broader, narrower))
        return overlaps

    @staticmethod
    def _parse_dependency_rule(rule: str) -> dict:
        rule = rule.strip()

        if "<-" in rule:
            raise ConfigError(
                "invalid arrow '<-'. Use '->' (e.g., 'api -> domain' means api can use domain)"
            )

        if "->" not in rule:
            raise ConfigError("missing '->'. Example: 'api -> domain' means api can use domain")

        parts = rule.split("->", 1)
        source, target = parts[0].strip(), parts[1].strip()

        if not source or not target:
            raise ConfigError("empty source or target")

        if source == "*" and target == "*":
            raise ConfigError("'* -> *' is not allowed — it would permit everything")

        for path in (source, target):
            if path == "*":
                continue
            if path.startswith(("/", "\\")) or ".." in path:
                raise ConfigError(f"invalid path: {path}")

        return {"from": source, "to": target, "original": rule}

    # ------------------------------------------------------------------
    # Overlap check
    # ------------------------------------------------------------------

    @classmethod
    def _broader_of(cls, rule1: dict, rule2: dict) -> dict | None:
        """Return the broader rule of an overlapping pair, or ``None`` if no overlap.

        Two rules overlap when one rule's source path is an ancestor of the
        other's *and* their targets cover the same area. Wildcard (``*``)
        rules never overlap with specific rules.
        """
        src1, src2 = rule1["from"], rule2["from"]
        tgt1, tgt2 = rule1["to"], rule2["to"]
        if "*" in (src1, src2, tgt1, tgt2):
            return None
        if cls._is_parent_path(src1, src2) and cls._paths_overlap(tgt1, tgt2):
            return rule1
        if cls._is_parent_path(src2, src1) and cls._paths_overlap(tgt1, tgt2):
            return rule2
        return None

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

        # Discover internal packages: top-level directories inside the service.
        internal_packages = {
            d.name
            for d in service_dir.iterdir()
            if d.is_dir() and not d.name.startswith((".", "_"))
        }

        violations: list[RuleViolation] = []

        # iter_py_files prunes vendored / cache directories; the AST cache
        # in collect_imports means sibling rules (no_circular_imports,
        # service_isolation) reuse the same parsed result for each file.
        for py_file in iter_py_files(service_dir):
            try:
                rel_path = py_file.relative_to(service_dir)
            except ValueError:
                continue
            module_path = rel_path.parent.as_posix()
            if module_path == ".":
                module_path = ""

            # Files at the service root (main.py, __init__.py, etc.) are not
            # inside any named package — dependency rules don't apply to them.
            if not module_path:
                continue

            for imp in collect_imports(py_file):
                if not imp.module:
                    continue
                # Skip stdlib (relative imports are always internal).
                if not imp.is_relative:
                    top = imp.module.split(".", 1)[0]
                    if top in STDLIB_MODULES:
                        continue

                imported_module = self._resolve_import(imp.module, module_path)

                # Skip third-party libs — only check imports whose root folder
                # actually exists inside the service directory.
                top_level = imported_module.split("/")[0]
                if top_level not in internal_packages:
                    continue

                if not self._is_import_allowed(module_path, imported_module, allowed_deps):
                    violations.append(
                        RuleViolation(
                            rule_name=self.rule_name,
                            service_name=self._service_spec.name,
                            severity="error",
                            message=f"Forbidden import in {rel_path}: '{imp.module}'",
                            file=str(rel_path),
                            line=imp.lineno or None,
                            details={
                                "from_module": module_path or "(root)",
                                "imported": imported_module,
                                "import_statement": imp.module,
                            },
                        )
                    )

        # Deterministic order for downstream consumers (CLI text output, JSON
        # diffs in CI). Sort once at the end rather than sorting the file
        # walk on every run.
        violations.sort(key=lambda v: (v.file or "", v.line or 0, v.message))
        return violations

    @staticmethod
    def _resolve_import(imp: str, current_module: str) -> str:
        """Resolve an import string to a service-relative folder path.

        Parameters
        ----------
        imp : str
            Raw import string, e.g. ``"domain.models"`` or ``"..utils"``.
        current_module : str
            The ``/``-separated folder of the file being analysed,
            e.g. ``"api/controllers"``.

        Returns
        -------
        str
            Service-relative path, e.g. ``"domain/models"``.
        """
        if not imp.startswith("."):
            # Absolute import — convert dots to slashes to get the full path
            return imp.replace(".", "/")

        # Relative import: delegate to the shared resolver. ``_resolve_relative``
        # treats the dot count as "go up that many levels" relative to *current*,
        # whereas Python semantics in a module file (current points at the file's
        # parent package) expect one less hop, so we synthesise a fake child.
        synthetic_current = f"{current_module}/_" if current_module else "_"
        resolved = _resolve_relative(imp, synthetic_current) or ""
        return resolved

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
