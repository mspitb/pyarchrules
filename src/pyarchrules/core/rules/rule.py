from abc import ABC, abstractmethod

from pyarchrules.model.rules.rule_violation import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class Rule(ABC):

    def __init__(self, service_spec: ServiceSpec):
        self._service_spec = service_spec

    @abstractmethod
    def validate(self) -> list[RuleViolation]:
        raise NotImplementedError

    @property
    @abstractmethod
    def rule_name(self) -> str:
        raise NotImplementedError
