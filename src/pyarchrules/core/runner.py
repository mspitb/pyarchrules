"""Runs rules and turns their violations into a result."""

from __future__ import annotations

from collections.abc import Iterable

from pyarchrules.core.errors import ValidationError
from pyarchrules.core.reporting import ConsoleViolationReporter, ViolationReporter
from pyarchrules.core.rules.rule import Rule
from pyarchrules.model.rules.rule_eval_result import RuleEvalResult


class RuleRunner:
    """Evaluates a collection of rules and reports / raises on violations."""

    def __init__(self, rules: Iterable[Rule]):
        self._rules = list(rules)

    def run(
        self,
        *,
        raise_on_violation: bool,
        verbose: bool,
        reporter: ViolationReporter | None = None,
    ) -> RuleEvalResult:
        """Run every rule.

        Parameters
        ----------
        raise_on_violation : bool
            Raise :class:`ValidationError` when the result contains violations.
        verbose : bool
            Send a failing result to *reporter*.
        reporter : ViolationReporter, optional
            Defaults to :class:`ConsoleViolationReporter` (stderr).
        """
        result = RuleEvalResult(
            violations=[violation for rule in self._rules for violation in rule.validate()]
        )

        if result.is_valid:
            return result

        if verbose:
            (reporter or ConsoleViolationReporter()).report(result)

        if raise_on_violation:
            message = f"Validation failed: {result.error_count} error(s)"
            if result.warning_count:
                message += f", {result.warning_count} warning(s)"
            raise ValidationError(message)

        return result
