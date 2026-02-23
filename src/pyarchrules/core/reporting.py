from __future__ import annotations

from typing import Protocol

from loguru import logger

from pyarchrules.model.rules.rule_eval_result import RuleEvalResult


class ViolationReporter(Protocol):
    """Protocol for objects that can report a
    :class:`~pyarchrules.model.rules.rule_eval_result.RuleEvalResult`."""

    def report(self, result: RuleEvalResult) -> None:
        """Output the validation result.

        Parameters
        ----------
        result : RuleEvalResult
            The result to report.
        """
        ...


class ConsoleViolationReporter:
    """Reports validation results to the console via :mod:`loguru`."""

    def report(self, result: RuleEvalResult) -> None:
        """Log all violations to stderr using :func:`loguru.logger.error`.

        Parameters
        ----------
        result : RuleEvalResult
            The result to report.
        """
        logger.error(
            "Architecture validation failed: {} error(s), {} warning(s)",
            result.error_count,
            result.warning_count,
        )
        for violation in result.violations:
            logger.error(violation.to_log_message())
