"""Base registry for rule management."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pyarchrules.core.errors import ValidationError
from pyarchrules.core.reporting import ConsoleViolationReporter, ViolationReporter
from pyarchrules.model.rules.rule_eval_result import RuleEvalResult


class BaseRegistry(ABC):
    """Base registry mapping service names to a rule container.

    Subclasses must implement :meth:`collect_violations` to traverse
    their specific store type.
    """

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Storage helpers
    # ------------------------------------------------------------------

    def get(self, service_name: str, default: Any = None) -> Any:
        """Return the entry for *service_name*, or *default* if absent."""
        return self._store.get(service_name, default)

    def get_all(self) -> dict[str, Any]:
        """Return a shallow copy of the full registry."""
        return dict(self._store)

    # ------------------------------------------------------------------
    # Violation pipeline
    # ------------------------------------------------------------------

    @abstractmethod
    def collect_violations(self) -> list:
        """Collect and return all violations from every registered entry."""

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
            Raise :class:`~pyarchrules.core.errors.ValidationError` when errors are found.
        verbose : bool, optional
            Log violations via the supplied *reporter* when ``True``.
        reporter : ViolationReporter, optional
            Custom reporter; falls back to
            :class:`~pyarchrules.core.reporting.ConsoleViolationReporter`.

        Returns
        -------
        RuleEvalResult
        """
        result = RuleEvalResult(violations=self.collect_violations())

        if verbose and not result.is_valid:
            (reporter or ConsoleViolationReporter()).report(result)

        if raise_on_violation and not result.is_valid:
            error_msg = f"Validation failed: {result.error_count} error(s)"
            if result.warning_count:
                error_msg += f", {result.warning_count} warning(s)"
            raise ValidationError(error_msg)

        return result
