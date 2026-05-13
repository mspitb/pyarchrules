from dataclasses import replace

from pyarchrules.core.errors import ConfigError
from pyarchrules.core.rules.dsl import NoCircularImportsRule
from pyarchrules.core.rules.linter.dependencies_rule import DependenciesRule
from pyarchrules.core.rules.linter.tree_rule import TreeRule
from pyarchrules.core.rules.rule import Rule
from pyarchrules.model.spec.service_spec import ServiceSpec, TreeMode


class ServiceRuleSet:
    """Fluent builder for attaching DSL rules to a service.

    The DSL mirrors the ``pyproject.toml`` configuration surface — all three
    architecture rules (:meth:`tree_structure`, :meth:`dependencies`,
    :meth:`no_circular_imports`) can be expressed in Python instead of, or in
    addition to, ``pyproject.toml``.

    Each method appends a rule and returns ``self`` so calls can be chained::

        rules.for_service("api") \\
             .tree_structure(["domain", "application", "infrastructure"], mode="strict") \\
             .dependencies(["application -> domain", "infrastructure -> domain"]) \\
             .no_circular_imports()

    DSL rules and ``pyproject.toml`` linter rules are evaluated independently
    (via :meth:`PyArchRules.validate` and :meth:`PyArchRules.check_linter`
    respectively).  Defining the same rule in both places is allowed — both
    will run and may report.  Keeping them consistent is the caller's
    responsibility.

    Parameters
    ----------
    service_spec : ServiceSpec
        Specification of the service these rules apply to.
    """

    def __init__(self, service_spec: ServiceSpec):
        self._service_spec = service_spec
        self._rules: list[Rule] = []

    # ------------------------------------------------------------------
    # Rule builders
    # ------------------------------------------------------------------

    def tree_structure(
        self,
        tree: list[str],
        *,
        mode: TreeMode | str = TreeMode.EXISTS,
        allow_files: bool = True,
        ignore: list[str] | None = None,
    ) -> "ServiceRuleSet":
        """Validate the service's directory layout.

        Mirrors the ``tree`` / ``tree_mode`` / ``tree_allow_files`` /
        ``tree_ignore`` keys in ``pyproject.toml``; see
        :class:`~pyarchrules.core.rules.linter.tree_rule.TreeRule`
        for the semantics of each mode.

        Parameters
        ----------
        tree : list[str]
            Required directory/file paths relative to the service root.
            Duplicate entries raise :class:`ConfigError`.
        mode : TreeMode or str, optional
            ``"exists"`` (default), ``"strict"`` or ``"exact"``.
        allow_files : bool, optional
            In ``strict``/``exact`` mode, tolerate loose files (default ``True``).
        ignore : list[str], optional
            Glob patterns of directory basenames to skip in
            ``strict``/``exact`` mode (e.g. ``["__snapshots__", "migrations"]``).

        Returns
        -------
        ServiceRuleSet

        Raises
        ------
        ConfigError
            If *mode* is not a valid :class:`TreeMode`, or *tree* contains
            duplicate entries.
        """
        tree = list(tree)
        seen: set[str] = set()
        duplicates: list[str] = []
        for entry in tree:
            if entry in seen and entry not in duplicates:
                duplicates.append(entry)
            seen.add(entry)
        if duplicates:
            raise ConfigError(
                f"Service '{self._service_spec.name}': duplicate entries in 'tree': {duplicates}"
            )

        if isinstance(mode, str):
            try:
                mode = TreeMode(mode)
            except ValueError:
                valid = ", ".join(f'"{m.value}"' for m in TreeMode)
                raise ConfigError(
                    f"Service '{self._service_spec.name}': invalid tree_mode "
                    f"'{mode}'. Valid values: {valid}"
                ) from None

        spec = replace(
            self._service_spec,
            tree=tree,
            tree_mode=mode,
            tree_allow_files=allow_files,
            tree_ignore=list(ignore or []),
        )
        self._rules.append(TreeRule(spec))
        return self

    def dependencies(self, rules: list[str]) -> "ServiceRuleSet":
        """Constrain internal import flow within the service.

        Mirrors the ``dependencies`` key in ``pyproject.toml``.  Strings use
        the same grammar (``"source -> target"``) and are parsed by
        :meth:`DependenciesRule.parse_rules`; malformed or overlapping rules
        raise :class:`ConfigError` immediately.

        Parameters
        ----------
        rules : list[str]
            Strings like ``"api -> domain"``.

        Returns
        -------
        ServiceRuleSet

        Raises
        ------
        ConfigError
            On malformed syntax, ``* -> *``, invalid paths, or overlapping pairs.
        """
        rules = list(rules)
        # Eager validation — same code path as the TOML loader.
        DependenciesRule.parse_rules(rules, service_name=self._service_spec.name)

        spec = replace(self._service_spec, dependencies=rules)
        self._rules.append(DependenciesRule(spec))
        return self

    def no_circular_imports(self, folder: str | None = None) -> "ServiceRuleSet":
        """Detect circular import chains using AST + DFS.

        Parameters
        ----------
        folder : str, optional
            Restrict the scan to this sub-path; defaults to the service root.

        Returns
        -------
        ServiceRuleSet
        """
        self._rules.append(NoCircularImportsRule(self._service_spec, folder=folder))
        return self

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def collect_violations(self) -> list:
        violations = []
        for rule in self._rules:
            violations.extend(rule.validate())
        return violations
