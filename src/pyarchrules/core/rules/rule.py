"""Base class for architecture rules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Literal

from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class Rule(ABC):
    """Base class for all architecture rules (Template Method).

    :meth:`validate` is fixed: it first checks that the service directory
    exists and then delegates to :meth:`_check`, which subclasses implement.

    Adding a rule
    -------------
    Pick the entry points the rule needs by also inheriting:

    * :class:`~pyarchrules.core.rules.linter.base.LinterRule` — enabled from
      TOML / CLI; implement ``from_spec`` and add the class to ``RULE_TYPES``
      in ``factory.py``.
    * :class:`~pyarchrules.core.rules.dsl.base.DslRule` — attached from Python;
      set ``dsl_method`` and add that method to ``ServiceRuleSet``.

    ``service_isolation`` is linter-only; the other rules inherit both.

    Parameters
    ----------
    service_spec : ServiceSpec
        Specification of the service this rule is evaluated against.
    """

    #: Identifier used in violation reports and by ``--rule`` filtering.
    name: ClassVar[str]

    def __init__(self, service_spec: ServiceSpec):
        self._service_spec = service_spec

    @property
    def rule_name(self) -> str:
        return self.name

    def validate(self) -> list[RuleViolation]:
        """Evaluate the rule and return its violations (empty when it passes)."""
        if not self._service_spec.absolute_path.exists():
            return [self._violation(f"Service directory does not exist: {self._service_spec.path}")]
        return self._check()

    @abstractmethod
    def _check(self) -> list[RuleViolation]:
        """Rule-specific logic; the service directory is known to exist."""

    def _violation(
        self,
        message: str,
        severity: Literal["error", "warning"] = "error",
        **fields,
    ) -> RuleViolation:
        return RuleViolation(
            rule_name=self.name,
            service_name=self._service_spec.name,
            message=message,
            severity=severity,
            **fields,
        )
