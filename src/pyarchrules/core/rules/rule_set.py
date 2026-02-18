from pyarchrules.core.rules.must_contain_folders_rule import MustContainFoldersRule
from pyarchrules.core.rules.rule import Rule
from pyarchrules.model.rules import RuleEvalResult
from pyarchrules.model.spec.service_spec import ServiceSpec


class ServiceRuleSet:

    def __init__(self, service_spec: ServiceSpec):
        self._service_spec = service_spec
        self._rules: list[Rule] = []

    def must_contain_folders(
        self, folders: list[str], allow_extra: bool = True
    ) -> "ServiceRuleSet":
        self._rules.append(
            MustContainFoldersRule(
                service_spec=self._service_spec, required_folders=folders, allow_extra=allow_extra
            )
        )
        return self

    def validate(self) -> RuleEvalResult:
        violations = []

        for rule in self._rules:
            rule_violations = rule.validate()
            violations.extend(rule_violations)

        return RuleEvalResult(violations=violations)
