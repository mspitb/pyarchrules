from __future__ import annotations

from typing import Protocol

from loguru import logger

from pyarchrules.model.rules.rule_eval_result import RuleEvalResult


class ViolationReporter(Protocol):
    def report(self, result: RuleEvalResult) -> None:
        raise NotImplementedError


class ConsoleViolationReporter:
    def report(self, result: RuleEvalResult) -> None:
        logger.error(
            "Architecture validation failed: {} error(s), {} warning(s)",
            result.error_count,
            result.warning_count,
        )
        for violation in result.violations:
            logger.error(violation.to_log_message())
