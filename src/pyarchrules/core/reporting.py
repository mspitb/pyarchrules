"""Reporting sinks for validation results."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from typing import Literal, Protocol, TextIO

from pyarchrules.model.rules.rule_eval_result import RuleEvalResult

ReporterFormat = Literal["text", "json"]


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
    """Reports validation results to a text stream (defaults to ``stderr``).

    Parameters
    ----------
    stream : TextIO, optional
        Destination stream; defaults to :data:`sys.stderr`.
    format : {"text", "json"}, optional
        Output format. ``"text"`` (default) writes a one-line summary plus
        each violation; ``"json"`` writes a single JSON document with a
        machine-readable schema suitable for CI integration.
    """

    def __init__(
        self,
        stream: TextIO | None = None,
        format: ReporterFormat = "text",
    ) -> None:
        self._stream = stream if stream is not None else sys.stderr
        self._format: ReporterFormat = format

    def report(self, result: RuleEvalResult) -> None:
        """Render *result* to the configured stream in the configured format."""
        if self._format == "json":
            self._report_json(result)
        else:
            self._report_text(result)

    # ------------------------------------------------------------------
    # Formatters
    # ------------------------------------------------------------------

    def _report_text(self, result: RuleEvalResult) -> None:
        print(
            f"Architecture validation failed: "
            f"{result.error_count} error(s), {result.warning_count} warning(s)",
            file=self._stream,
        )
        for violation in result.violations:
            print(violation.to_log_message(), file=self._stream)

    def _report_json(self, result: RuleEvalResult) -> None:
        payload = {
            "summary": {
                "errors": result.error_count,
                "warnings": result.warning_count,
                "is_valid": result.is_valid,
            },
            "violations": [asdict(v) for v in result.violations],
        }
        json.dump(payload, self._stream, indent=2, sort_keys=True, default=str)
        self._stream.write("\n")
