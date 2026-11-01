"""Interface for rules that can be enabled from ``[tool.pyarchrules]``."""

from __future__ import annotations

from abc import abstractmethod

from pyarchrules.core.rules.rule import Rule
from pyarchrules.model.spec.project_spec import ProjectSpec
from pyarchrules.model.spec.service_spec import ServiceSpec


class LinterRule(Rule):
    """A rule built from configuration (TOML / CLI).

    Subclasses must also be listed in ``RULE_TYPES`` in ``factory.py``;
    new configuration keys belong on ``ServiceSpec``.
    """

    @classmethod
    @abstractmethod
    def from_spec(cls, service_spec: ServiceSpec, project_spec: ProjectSpec) -> LinterRule | None:
        """Build the rule from configuration, or return ``None`` when it is not enabled."""
