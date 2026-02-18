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
        if path is None:
            path = Path.cwd()

        path = Path(path).resolve()
        if path.is_file():
            path = path.parent

        self._project_root = self._find_project_root(path)
        self._project_spec: ProjectSpec = SpecLoader(self._project_root).load()

        self.services = {name: spec.path for name, spec in self._project_spec.services.items()}

        # Registries for rules
        self._dsl_registry = DSLRegistry()
        self._linter_registry = LinterRegistry()

    @property
    def project_root(self) -> Path:
        """Get the project root path."""
        return self._project_root

    @property
    def project_spec(self) -> ProjectSpec:
        """Get the full project specification."""
        return self._project_spec

    @property
    def dsl_registry(self) -> DSLRegistry:
        """Get the DSL registry."""
        return self._dsl_registry

    @property
    def linter_registry(self) -> LinterRegistry:
        """Get the linter registry."""
        return self._linter_registry

    def for_service(self, service_name: str) -> ServiceRuleSet:
        if service_name not in self._project_spec.services:
            available = ", ".join(f"'{s}'" for s in self._project_spec.services.keys())
            raise PyArchError(
                f"Service '{service_name}' not found in configuration. "
                f"Available services: {available}"
            )

        # Check if already registered in DSL registry
        existing = self._dsl_registry.get(service_name)
        if existing is not None:
            return existing

        # Create new RuleSet with the new ServiceSpec
        service_spec = self._project_spec.services[service_name]
        service_rules = ServiceRuleSet(service_spec)

        # Register in DSL registry
        self._dsl_registry.register(service_name, service_rules)

        return service_rules

    def validate(
        self,
        raise_on_violation: bool = True,
        verbose: bool = True,
        reporter: ViolationReporter | None = None,
    ) -> RuleEvalResult:
        all_violations = []

        # Validate DSL rules
        for service_name, service_rules in self._dsl_registry.get_all().items():
            all_violations.extend(service_rules.validate().violations)

        # Validate linter rules
        for service_name, rules in self._linter_registry.get_all().items():
            for rule in rules:
                all_violations.extend(rule.validate())

        final_result = RuleEvalResult(violations=all_violations)

        if verbose and not final_result.is_valid:
            (reporter or ConsoleViolationReporter()).report(final_result)

        if raise_on_violation and not final_result.is_valid:
            error_msg = f"Architecture validation failed with {final_result.error_count} error(s)"
            if final_result.warning_count > 0:
                error_msg += f" and {final_result.warning_count} warning(s)"
            raise PyArchError(error_msg)

        return final_result

    def _find_project_root(self, start: Path) -> Path:
        for parent in [start, *start.parents]:
            if (parent / "pyproject.toml").exists():
                return parent
        raise PyArchError("pyproject.toml not found in current or parent directories")
