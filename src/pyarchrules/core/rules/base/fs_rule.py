"""FsBaseRule — base class for all file-system inspection rules."""

from __future__ import annotations

from abc import abstractmethod
from pathlib import Path

from pyarchrules.core.rules.rule import Rule
from pyarchrules.model.rules.rule_violation import RuleViolation


class FsBaseRule(Rule):
    """Base rule that resolves a target directory and delegates checking.

    Subclasses implement :meth:`_check_directory` to produce violations for a path.

    Parameters
    ----------
    service_spec : ServiceSpec
        Specification of the service being validated.
    folder : str, optional
        Sub-path relative to the service root to restrict inspection to.
        When ``None`` the service root itself is used.
    """

    def __init__(self, service_spec, folder: str | None = None):
        super().__init__(service_spec)
        self._folder = folder

    # ------------------------------------------------------------------
    # Public Rule interface
    # ------------------------------------------------------------------

    def validate(self) -> list[RuleViolation]:
        """Run the rule against the resolved target directory.

        Returns
        -------
        list[RuleViolation]
            Empty list when the directory passes, or a single error violation
            when the directory does not exist, otherwise whatever
            :meth:`_check_directory` returns.
        """
        target = self._resolve_target()
        if not target.exists():
            return [
                RuleViolation(
                    rule_name=self.rule_name,
                    service_name=self._service_spec.name,
                    severity="error",
                    message=(
                        "Directory does not exist: "
                        f"{target.relative_to(self._service_spec.project_root)}"
                    ),
                )
            ]
        return self._check_directory(target)

    # ------------------------------------------------------------------
    # Hook for subclasses
    # ------------------------------------------------------------------

    @abstractmethod
    def _check_directory(self, directory: Path) -> list[RuleViolation]:
        """Inspect the resolved directory and return any violations.

        Parameters
        ----------
        directory : Path
            Absolute path to the directory to inspect.

        Returns
        -------
        list[RuleViolation]
            All violations found inside *directory*.
        """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_target(self) -> Path:
        """Return the absolute path this rule should inspect.

        Returns
        -------
        Path
            ``service_root / folder`` when *folder* was supplied,
            otherwise the service root itself.
        """
        base = self._service_spec.absolute_path
        return base / self._folder if self._folder else base

    def _make_violation(
        self, message: str, severity: str = "error", details: dict | None = None
    ) -> RuleViolation:
        """Build a :class:`~pyarchrules.model.rules.rule_violation.RuleViolation` for this rule.

        Parameters
        ----------
        message : str
            Human-readable description of what went wrong.
        severity : str, optional
            ``"error"`` (default) or ``"warning"``.
        details : dict, optional
            Extra context attached to the violation.

        Returns
        -------
        RuleViolation
            Violation populated with this rule's name and service name.
        """
        return RuleViolation(
            rule_name=self.rule_name,
            service_name=self._service_spec.name,
            severity=severity,  # type: ignore[arg-type]
            message=message,
            details=details or {},
        )
