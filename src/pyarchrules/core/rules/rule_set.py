"""Fluent builder for attaching rules to a service from Python code."""

from __future__ import annotations

from dataclasses import replace

from pyarchrules.core.rules.dependencies_rule import DependenciesRule
from pyarchrules.core.rules.no_circular_imports_rule import NoCircularImportsRule
from pyarchrules.core.rules.rule import Rule
from pyarchrules.core.rules.tree_rule import TreeRule
from pyarchrules.model.spec.service_spec import ServiceSpec, TreeMode


class ServiceRuleSet:
    """Fluent builder (DSL) for attaching rules to a service.

    The DSL mirrors the ``pyproject.toml`` keys — :meth:`tree_structure`,
    :meth:`dependencies` and :meth:`no_circular_imports` — and every call
    returns ``self`` so calls can be chained::

        rules.for_service("api") \\
             .tree_structure(["domain", "application", "infrastructure"], mode="strict") \\
             .dependencies(["application -> domain", "infrastructure -> domain"]) \\
             .no_circular_imports()

    DSL rules (run by :meth:`PyArchRules.validate`) and ``pyproject.toml`` rules
    (run by :meth:`PyArchRules.check_linter`) are independent of each other.
    Arguments are validated by :class:`ServiceSpec`, so invalid input raises
    :class:`~pyarchrules.core.errors.ConfigError` immediately.

    Parameters
    ----------
    service_spec : ServiceSpec
        Specification of the service these rules apply to.
    """

    def __init__(self, service_spec: ServiceSpec):
        self._service_spec = service_spec
        self._rules: list[Rule] = []

    @property
    def rules(self) -> list[Rule]:
        """Rules attached so far."""
        return list(self._rules)

    def tree_structure(
        self,
        tree: list[str],
        *,
        mode: TreeMode = TreeMode.EXISTS,
        allow_files: bool = True,
        ignore: list[str] | None = None,
    ) -> ServiceRuleSet:
        """Validate the service's directory layout.

        Parameters
        ----------
        tree : list[str]
            Required paths relative to the service root; duplicates are rejected.
        mode : TreeMode or str, optional
            ``"exists"`` (default), ``"strict"`` or ``"exact"``; see
            :class:`~pyarchrules.core.rules.tree_rule.TreeRule`.
        allow_files : bool, optional
            In ``strict`` / ``exact`` mode, tolerate loose files (default ``True``).
        ignore : list[str], optional
            Glob patterns of directory names skipped in ``strict`` / ``exact`` mode.

        Raises
        ------
        ConfigError
            On an invalid *mode* or duplicate *tree* entries.
        """
        spec = replace(
            self._service_spec,
            tree=tree,
            tree_mode=mode,
            tree_allow_files=allow_files,
            tree_ignore=ignore or [],
        )
        self._rules.append(TreeRule(spec))
        return self

    def dependencies(self, rules: list[str]) -> ServiceRuleSet:
        """Constrain internal import flow, e.g. ``["api -> domain"]``.

        Raises
        ------
        ConfigError
            On malformed syntax, ``* -> *`` or invalid paths.
        """
        spec = replace(self._service_spec, dependencies=rules)
        self._rules.append(DependenciesRule(spec))
        return self

    def no_circular_imports(self, folder: str | None = None) -> ServiceRuleSet:
        """Report circular imports.

        Parameters
        ----------
        folder : str, optional
            Restrict the scan to this sub-path; defaults to the service root.
        """
        self._rules.append(NoCircularImportsRule(self._service_spec, folder=folder))
        return self
