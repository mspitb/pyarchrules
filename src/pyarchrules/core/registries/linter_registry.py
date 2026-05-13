"""Registry for linter rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pyarchrules.core.registries.base_registry import BaseRegistry
from pyarchrules.core.rules.dsl.no_circular_imports_rule import NoCircularImportsRule
from pyarchrules.core.rules.linter import DependenciesRule, ServiceIsolationRule, TreeRule

if TYPE_CHECKING:
    from pyarchrules.core.rules.rule import Rule
    from pyarchrules.model.spec.project_spec import ProjectSpec


# Rule classes contributing TOML keys to [tool.pyarchrules.services.<name>].
# Each rule advertises its keys via the ``CONFIG_KEYS`` ClassVar; the spec
# loader uses :meth:`LinterRegistry.known_service_keys` so the allow-list
# never drifts from the registered rule set.
_LINTER_RULES: tuple[type, ...] = (
    TreeRule,
    DependenciesRule,
    NoCircularImportsRule,
    ServiceIsolationRule,
)


class LinterRegistry(BaseRegistry):
    """Registry for linter rules derived from ``pyproject.toml`` configuration.

    When a :class:`~pyarchrules.model.spec.project_spec.ProjectSpec` is supplied,
    rules are auto-registered from the spec on construction.

    Parameters
    ----------
    project_spec : ProjectSpec, optional
        When provided, rules are automatically registered for every service.
    """

    def __init__(self, project_spec: ProjectSpec | None = None) -> None:
        super().__init__()
        if project_spec is not None:
            self._load_from_spec(project_spec)

    def register(self, service_name: str, rule: Rule) -> None:
        """Register a single rule for *service_name*.

        Parameters
        ----------
        service_name : str
        rule : Rule
        """
        self._store.setdefault(service_name, []).append(rule)

    @classmethod
    def known_service_keys(cls) -> frozenset[str]:
        """Return the full set of supported keys under
        ``[tool.pyarchrules.services.<name>]``.

        Aggregates ``CONFIG_KEYS`` from every registered linter rule plus the
        always-required ``"path"`` key.
        """
        keys: set[str] = {"path"}
        for rule_cls in _LINTER_RULES:
            keys.update(getattr(rule_cls, "CONFIG_KEYS", frozenset()))
        return frozenset(keys)

    # ------------------------------------------------------------------
    # Violation collection
    # ------------------------------------------------------------------

    def collect_violations(self) -> list:
        """Collect all violations from every registered linter rule."""
        violations = []
        for rules in self._store.values():
            for rule in rules:
                violations.extend(rule.validate())
        return violations

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_from_spec(self, project_spec: ProjectSpec) -> None:
        for service_name, service_spec in project_spec.services.items():
            rules: list[Rule] = []

            if service_spec.tree:
                rules.append(TreeRule(service_spec))
            if service_spec.dependencies:
                rules.append(DependenciesRule(service_spec))
            if service_spec.no_circular_imports:
                rules.append(NoCircularImportsRule(service_spec))
            # Project-level isolate_services: every non-shared service gets
            # a ServiceIsolationRule. Shared services skip the rule (they
            # are intentionally importable by everyone).
            if project_spec.isolate_services and not service_spec.shared:
                rules.append(ServiceIsolationRule(service_spec, project_spec))

            for rule in rules:
                self.register(service_name, rule)
