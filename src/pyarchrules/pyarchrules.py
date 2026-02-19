from __future__ import annotations

from pathlib import Path

from pyarchrules.core.errors import PyArchError
from pyarchrules.core.registries import DSLRegistry, LinterRegistry
from pyarchrules.core.reporting import ConsoleViolationReporter, ViolationReporter
from pyarchrules.core.rules.rule_set import ServiceRuleSet
from pyarchrules.core.spec_loader import SpecLoader
from pyarchrules.model.rules import RuleEvalResult
from pyarchrules.model.spec import ProjectSpec


class PyArchRules:
    def __init__(self, path: str | Path | None = None):
        path = Path(path or Path.cwd()).resolve()
        if path.is_file():
            path = path.parent

        self._project_root = self._find_project_root(path)
        self._project_spec: ProjectSpec = SpecLoader(self._project_root).load()
        self.services = {name: spec.path for name, spec in self._project_spec.services.items()}

        self._dsl_registry = DSLRegistry()
        self._linter_registry = LinterRegistry()
        self._load_linter_rules()

    @property
    def project_root(self) -> Path:
        return self._project_root

    @property
    def project_spec(self) -> ProjectSpec:
        return self._project_spec

    @property
    def dsl_registry(self) -> DSLRegistry:
        return self._dsl_registry

    @property
    def linter_registry(self) -> LinterRegistry:
        return self._linter_registry

    def for_service(self, service_name: str) -> ServiceRuleSet:
        if service_name not in self._project_spec.services:
            available = ", ".join(f"'{s}'" for s in self._project_spec.services.keys())
            raise PyArchError(f"Service '{service_name}' not found. Available: {available}")

        existing = self._dsl_registry.get(service_name)
        if existing is not None:
            return existing

        service_spec = self._project_spec.services[service_name]
        service_rules = ServiceRuleSet(service_spec)
        self._dsl_registry.register(service_name, service_rules)

        return service_rules

    def _load_linter_rules(self) -> None:
        from pyarchrules.core.rules.linter import (
            AllowedServiceDependenciesRule,
            DependenciesRule,
            TreeRule,
        )

        for service_name, service_spec in self._project_spec.services.items():
            linter_rules = []

            if service_spec.tree:
                linter_rules.append(TreeRule(service_spec))
            if service_spec.allowed_service_dependencies:
                linter_rules.append(AllowedServiceDependenciesRule(service_spec))
            if service_spec.dependencies:
                linter_rules.append(DependenciesRule(service_spec))

            if linter_rules:
                self._linter_registry.register_many(service_name, linter_rules)

    def validate(
        self,
        raise_on_violation: bool = True,
        verbose: bool = True,
        reporter: ViolationReporter | None = None,
        run_dsl: bool = True,
        run_linter: bool = False,
    ) -> RuleEvalResult:
        all_violations = []

        if run_dsl:
            for service_rules in self._dsl_registry.get_all().values():
                all_violations.extend(service_rules.validate().violations)

        if run_linter:
            for rules in self._linter_registry.get_all().values():
                for rule in rules:
                    all_violations.extend(rule.validate())

        final_result = RuleEvalResult(violations=all_violations)

        if verbose and not final_result.is_valid:
            (reporter or ConsoleViolationReporter()).report(final_result)

        if raise_on_violation and not final_result.is_valid:
            error_msg = f"Validation failed: {final_result.error_count} error(s)"
            if final_result.warning_count:
                error_msg += f", {final_result.warning_count} warning(s)"
            raise PyArchError(error_msg)

        return final_result

    def _find_project_root(self, start: Path) -> Path:
        for parent in [start, *start.parents]:
            if (parent / "pyproject.toml").exists():
                return parent
        raise PyArchError("pyproject.toml not found in current or parent directories")
