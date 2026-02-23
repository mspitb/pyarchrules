from pyarchrules.core.rules.rule import Rule
from pyarchrules.model.rules import RuleViolation
from pyarchrules.model.spec.service_spec import ServiceSpec


class MustContainFoldersRule(Rule):
    MESSAGE_MISSING = "Missing required folders:"
    MESSAGE_EXTRA = "Extra folders not allowed:"

    def __init__(
        self,
        service_spec: ServiceSpec,
        required_folders: list[str],
        allow_extra: bool = True,
    ):
        super().__init__(service_spec)
        self._required_folders = required_folders
        self._allow_extra = allow_extra

    def validate(self) -> list[RuleViolation]:
        violations = []

        service_dir = self._service_spec.absolute_path

        if not service_dir.exists():
            violations.append(
                RuleViolation(
                    rule_name=self.rule_name,
                    service_name=self._service_spec.name,
                    severity="error",
                    message=f"Service directory '{service_dir}' does not exist.",
                )
            )

            return violations

        service_folders = {
            d.name for d in service_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
        }

        missing_folders = set(self._required_folders) - service_folders
        if missing_folders:
            missing_sorted = sorted(missing_folders)
            violations.append(
                RuleViolation(
                    rule_name=self.rule_name,
                    service_name=self._service_spec.name,
                    message=f"{self.MESSAGE_MISSING} {missing_sorted}",
                    details={"missing": missing_sorted, "actual": sorted(service_folders)},
                )
            )

        if not self._allow_extra:
            extra_folders = service_folders - set(self._required_folders)
            if extra_folders:
                extra_sorted = sorted(extra_folders)
                violations.append(
                    RuleViolation(
                        rule_name=self.rule_name,
                        service_name=self._service_spec.name,
                        message=f"{self.MESSAGE_EXTRA} {extra_sorted}",
                        severity="warning",
                        details={"extra": extra_sorted, "actual": sorted(service_folders)},
                    )
                )

        return violations

    @property
    def rule_name(self) -> str:
        return "must_contain_folders"
