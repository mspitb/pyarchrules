from __future__ import annotations

from pathlib import Path

from pyarchrules.core.errors import PyArchError
from pyarchrules.core.registries import DSLRegistry, LinterRegistry
from pyarchrules.core.reporting import ViolationReporter
from pyarchrules.core.rules.rule_set import ServiceRuleSet
from pyarchrules.core.spec_loader import SpecLoader
from pyarchrules.model.rules import RuleEvalResult
from pyarchrules.model.spec import ProjectSpec


class PyArchRules:
    """Entry point for programmatic architecture validation.

    Loads ``pyproject.toml`` from *path* (or the current working directory),
    builds DSL and linter rule registries, and exposes the validation API.

    Parameters
    ----------
    path : str or Path, optional
        A file or directory inside the project tree.  When omitted the
        current working directory is used.  The nearest ``pyproject.toml``
        in the directory tree is discovered automatically.
    """

    def __init__(self, path: str | Path | None = None):
        path = Path(path or Path.cwd()).resolve()
        if path.is_file():
            path = path.parent

        self._project_root = self._find_project_root(path)
        self._project_spec: ProjectSpec = SpecLoader(self._project_root).load()
        self._services = {name: spec.path for name, spec in self._project_spec.services.items()}

        self._dsl_registry = DSLRegistry(self._project_spec)
        self._linter_registry = LinterRegistry(self._project_spec)

    @property
    def project_root(self) -> Path:
        return self._project_root

    @property
    def project_spec(self) -> ProjectSpec:
        return self._project_spec

    @property
    def services(self) -> dict[str, Path]:
        """Return a mapping of service names to their paths."""
        return self._services

    @property
    def linter_rule_count(self) -> int:
        """Total number of linter rules across all services."""
        return sum(len(rules) for rules in self._linter_registry.get_all().values())

    def linter_rules_for(self, service_name: str) -> list:
        """Return the linter rules registered for *service_name*."""
        return self._linter_registry.get(service_name)

    # ------------------------------------------------------------------
    # DSL API
    # ------------------------------------------------------------------

    def for_service(self, service_name: str) -> ServiceRuleSet:
        rule_set = self._dsl_registry.get(service_name)
        if rule_set is None:
            available = ", ".join(f"'{s}'" for s in self._project_spec.services)
            raise PyArchError(f"Service '{service_name}' not found. Available: {available}")
        return rule_set

    def validate(
        self,
        raise_on_violation: bool = True,
        verbose: bool = True,
        reporter: ViolationReporter | None = None,
    ) -> RuleEvalResult:
        """Run all registered DSL rules and return the result."""
        return self._dsl_registry.validate(
            raise_on_violation=raise_on_violation,
            verbose=verbose,
            reporter=reporter,
        )

    # ------------------------------------------------------------------
    # Linter API
    # ------------------------------------------------------------------

    def check_linter(
        self,
        raise_on_violation: bool = False,
        verbose: bool = False,
        reporter: ViolationReporter | None = None,
    ) -> RuleEvalResult:
        """Run all linter rules loaded from ``pyproject.toml``.

        Parameters
        ----------
        raise_on_violation : bool, optional
            Raise :class:`~pyarchrules.core.errors.PyArchError` when errors are found.
        verbose : bool, optional
            Log violations via the supplied *reporter* when ``True``.
        reporter : ViolationReporter, optional
            Custom reporter; falls back to ``ConsoleViolationReporter``.

        Returns
        -------
        RuleEvalResult
        """
        return self._linter_registry.validate(
            raise_on_violation=raise_on_violation,
            verbose=verbose,
            reporter=reporter,
        )

    def _find_project_root(self, start: Path) -> Path:
        for parent in [start, *start.parents]:
            if (parent / "pyproject.toml").exists():
                return parent
        raise PyArchError("pyproject.toml not found in current or parent directories")
