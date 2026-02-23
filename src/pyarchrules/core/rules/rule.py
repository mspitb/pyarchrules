from abc import ABC, abstractmethod

from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class Rule(ABC):
    """Abstract base class for all architecture rules.

    Parameters
    ----------
    service_spec : ServiceSpec
        Specification of the service this rule will be evaluated against.
    """

    def __init__(self, service_spec: ServiceSpec):
        self._service_spec = service_spec

    @abstractmethod
    def validate(self) -> list[RuleViolation]:
        """Evaluate the rule and return any violations.

        Returns
        -------
        list[RuleViolation]
            Empty list when the rule passes, otherwise one or more violations.
        """
        ...

    @property
    @abstractmethod
    def rule_name(self) -> str:
        """Unique identifier for this rule used in violation reports.

        Returns
        -------
        str
        """
        ...
