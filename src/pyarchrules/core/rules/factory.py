"""Factory that turns a loaded configuration into rule instances."""

from __future__ import annotations

from pyarchrules.core.rules.dependencies_rule import DependenciesRule
from pyarchrules.core.rules.isolation_rule import ServiceIsolationRule
from pyarchrules.core.rules.linter import LinterRule
from pyarchrules.core.rules.no_circular_imports_rule import NoCircularImportsRule
from pyarchrules.core.rules.rule import Rule
from pyarchrules.core.rules.tree_rule import TreeRule
from pyarchrules.model.spec.project_spec import ProjectSpec
from pyarchrules.model.spec.service_spec import ServiceSpec

# Registered rule types; each decides via ``LinterRule.from_spec`` whether the
# configuration enables it.
RULE_TYPES: tuple[type[LinterRule], ...] = (
    TreeRule,
    DependenciesRule,
    NoCircularImportsRule,
    ServiceIsolationRule,
)


class RuleFactory:
    """Creates the rules enabled by a :class:`ProjectSpec`."""

    @staticmethod
    def create(service_spec: ServiceSpec, project_spec: ProjectSpec) -> list[Rule]:
        """Rules enabled for one service, in registration order."""
        rules = (rule_type.from_spec(service_spec, project_spec) for rule_type in RULE_TYPES)
        return [rule for rule in rules if rule is not None]

    @staticmethod
    def create_all(project_spec: ProjectSpec) -> dict[str, list[Rule]]:
        """Rules enabled for every service, keyed by service name."""
        return {
            name: RuleFactory.create(spec, project_spec)
            for name, spec in project_spec.services.items()
        }
