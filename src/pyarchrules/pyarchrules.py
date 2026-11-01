from __future__ import annotations

from pathlib import Path

from pyarchrules.core.errors import ConfigError, ServiceNotFoundError
from pyarchrules.core.reporting import ViolationReporter
from pyarchrules.core.rules.factory import RuleFactory
from pyarchrules.core.rules.rule import Rule
from pyarchrules.core.rules.rule_set import ServiceRuleSet
from pyarchrules.core.runner import RuleRunner
from pyarchrules.core.spec_loader import SpecLoader
from pyarchrules.model.rules import RuleEvalResult
from pyarchrules.model.spec import ProjectSpec, ServiceSpec


class PyArchRules:
    """Entry point for programmatic architecture validation.

    Three ways to construct one:

    * ``PyArchRules()`` / ``PyArchRules(path)`` — discover ``pyproject.toml``
      and load services from ``[tool.pyarchrules.services]``.
    * :meth:`from_services` — declare services in code, no TOML required.
    * :meth:`from_spec` — pass a pre-built :class:`ProjectSpec`.

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

        project_root = self._find_project_root(path)
        project_spec = SpecLoader(project_root).load()
        self._init_state(project_root, project_spec)

    @classmethod
    def from_services(
        cls,
        services: dict[str, str | Path],
        *,
        project_root: str | Path | None = None,
    ) -> PyArchRules:
        """Build a :class:`PyArchRules` without requiring ``pyproject.toml``.

        Useful for test-first workflows where architecture rules live entirely
        in Python (typically inside the test suite) and the project does not
        carry a ``[tool.pyarchrules]`` table.

        Parameters
        ----------
        services : dict[str, str or Path]
            Mapping of service name → directory path (relative to *project_root*).
        project_root : str or Path, optional
            Absolute path to the project root.  Defaults to the current
            working directory.

        Returns
        -------
        PyArchRules

        Raises
        ------
        ConfigError
            If *project_root* is not a directory, or any service path is
            missing or escapes the project root.
        """
        root = Path(project_root or Path.cwd()).resolve()
        if not root.is_dir():
            raise ConfigError(f"project_root does not exist or is not a directory: {root}")

        service_specs: dict[str, ServiceSpec] = {}
        for name, rel in services.items():
            rel_posix = str(rel).replace("\\", "/").rstrip("/") or "."
            full = (root / rel_posix).resolve()
            if not full.is_relative_to(root):
                raise ConfigError(f"Service '{name}' path is outside project root: {rel}")
            if not full.is_dir():
                raise ConfigError(f"Service '{name}' path doesn't exist: {rel}")
            service_specs[name] = ServiceSpec(name=name, path=rel_posix, project_root=root)

        return cls.from_spec(ProjectSpec(services=service_specs), project_root=root)

    @classmethod
    def from_spec(cls, spec: ProjectSpec, *, project_root: str | Path) -> PyArchRules:
        """Build a :class:`PyArchRules` from a pre-constructed :class:`ProjectSpec`.

        Power-user escape hatch for tests and tooling.  No filesystem
        validation is performed beyond resolving *project_root*.

        Parameters
        ----------
        spec : ProjectSpec
            Fully populated project specification.
        project_root : str or Path
            Absolute path to the project root.

        Returns
        -------
        PyArchRules
        """
        instance = cls.__new__(cls)
        instance._init_state(Path(project_root).resolve(), spec)
        return instance

    def _init_state(self, project_root: Path, project_spec: ProjectSpec) -> None:
        """Shared initialiser used by :meth:`__init__` and alternative constructors."""
        self._project_root = project_root
        self._project_spec = project_spec
        self._services = {name: spec.path for name, spec in project_spec.services.items()}
        self._rule_sets = {
            name: ServiceRuleSet(spec) for name, spec in project_spec.services.items()
        }
        self._config_rules: dict[str, list[Rule]] = RuleFactory.create_all(project_spec)

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
        return sum(len(rules) for rules in self._config_rules.values())

    def linter_rules_for(self, service_name: str) -> list[Rule]:
        """Return the `pyproject.toml` rules enabled for *service_name*."""
        return list(self._config_rules.get(service_name, []))

    def for_service(self, service_name: str) -> ServiceRuleSet:
        """Return the :class:`ServiceRuleSet` for *service_name*.

        Parameters
        ----------
        service_name : str
            Name of a service declared in ``[tool.pyarchrules.services]``.

        Returns
        -------
        ServiceRuleSet
            Fluent builder for attaching DSL rules to that service.

        Raises
        ------
        ServiceNotFoundError
            When *service_name* is not declared in the configuration.
        """
        rule_set = self._rule_sets.get(service_name)
        if rule_set is None:
            available = ", ".join(f"'{s}'" for s in self._project_spec.services)
            raise ServiceNotFoundError(
                f"Service '{service_name}' not found. Available: {available}"
            )
        return rule_set

    def validate(
        self,
        raise_on_violation: bool = True,
        verbose: bool = True,
        reporter: ViolationReporter | None = None,
    ) -> RuleEvalResult:
        """Run all registered DSL rules and return the result.

        Parameters
        ----------
        raise_on_violation : bool, optional
            When ``True`` (default), raise
            :class:`~pyarchrules.core.errors.ValidationError` if any
            error-severity violation is found.
        verbose : bool, optional
            When ``True`` (default), pass the result to *reporter* (or the
            default :class:`~pyarchrules.core.reporting.ConsoleViolationReporter`).
        reporter : ViolationReporter, optional
            Custom reporter implementation; defaults to console / stderr.

        Returns
        -------
        RuleEvalResult
            Aggregated violations across every DSL rule.
        """
        rules = [rule for rule_set in self._rule_sets.values() for rule in rule_set.rules]
        return RuleRunner(rules).run(
            raise_on_violation=raise_on_violation,
            verbose=verbose,
            reporter=reporter,
        )

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
            When ``True``, raise
            :class:`~pyarchrules.core.errors.ValidationError` on errors.
            Defaults to ``False`` so the CLI can format output itself.
        verbose : bool, optional
            When ``True``, pass the result to *reporter*. Defaults to ``False``.
        reporter : ViolationReporter, optional
            Custom reporter; falls back to
            :class:`~pyarchrules.core.reporting.ConsoleViolationReporter`.

        Returns
        -------
        RuleEvalResult
            Aggregated violations across every linter rule.
        """
        rules = [rule for service_rules in self._config_rules.values() for rule in service_rules]
        return RuleRunner(rules).run(
            raise_on_violation=raise_on_violation,
            verbose=verbose,
            reporter=reporter,
        )

    @staticmethod
    def _find_project_root(start: Path) -> Path:
        """Locate the nearest ancestor directory containing ``pyproject.toml``."""
        for parent in [start, *start.parents]:
            if (parent / "pyproject.toml").exists():
                return parent
        raise ConfigError("pyproject.toml not found in current or parent directories")
