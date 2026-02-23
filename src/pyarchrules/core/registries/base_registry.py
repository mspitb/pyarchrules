"""Base registry for rule management."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pyarchrules.core.errors import PyArchError
from pyarchrules.core.reporting import ConsoleViolationReporter, ViolationReporter
from pyarchrules.model.rules.rule_eval_result import RuleEvalResult


class BaseRegistry[V](ABC):
    """Generic base registry mapping service names to rule containers.

    Subclasses must implement :meth:`_collect_violations` to traverse
    their specific store type.
    """

    def __init__(self) -> None:
        self._store: dict[str, V] = {}

    # ------------------------------------------------------------------
    # Storage helpers
    # ------------------------------------------------------------------

    def get(self, service_name: str) -> V | None:
        """Return the entry for *service_name*, or ``None`` if absent.

        Parameters
        ----------
        service_name : str

        Returns
        -------
        V or None
        """
        return self._store.get(service_name)

    def get_all(self) -> dict[str, V]:
        """Return a shallow copy of the full registry.

        Returns
        -------
        dict[str, V]
        """
        return dict(self._store)

    def get_all_services(self) -> list[str]:
        """Return all service names that have a registered entry.

        Returns
        -------
        list[str]
        """
        return list(self._store.keys())

    def has(self, service_name: str) -> bool:
        """Return ``True`` if *service_name* has a registered entry.

        Parameters
        ----------
        service_name : str

        Returns
        -------
        bool
        """
        return service_name in self._store

    def clear(self) -> None:
        """Remove all entries from the registry."""
        self._store.clear()

    # ------------------------------------------------------------------
    # Violation pipeline
    # ------------------------------------------------------------------

    @abstractmethod
    def _collect_violations(self) -> list:
        """Collect and return all violations from every registered entry.

        Returns
        -------
        list[RuleViolation]
        """

    def validate(
        self,
        raise_on_violation: bool = True,
        verbose: bool = True,
        reporter: ViolationReporter | None = None,
    ) -> RuleEvalResult:
        """Run all rules, report violations, and optionally raise on failure.

        Parameters
        ----------
        raise_on_violation : bool, optional
            Raise :class:`~pyarchrules.core.errors.PyArchError` when errors are found.
        verbose : bool, optional
            Log violations via the supplied *reporter* when ``True``.
        reporter : ViolationReporter, optional
            Custom reporter; falls back to
            :class:`~pyarchrules.core.reporting.ConsoleViolationReporter`.

        Returns
        -------
        RuleEvalResult
        """
        result = RuleEvalResult(violations=self._collect_violations())

        if verbose and not result.is_valid:
            (reporter or ConsoleViolationReporter()).report(result)

        if raise_on_violation and not result.is_valid:
            error_msg = f"Validation failed: {result.error_count} error(s)"
            if result.warning_count:
                error_msg += f", {result.warning_count} warning(s)"
            raise PyArchError(error_msg)

        return result
