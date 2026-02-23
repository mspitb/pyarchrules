"""ImportBaseRule — base class for all import-inspection rules."""

from __future__ import annotations

from abc import abstractmethod
from pathlib import Path

from pyarchrules.core.rules.checks.imports import ImportInfo, collect_imports
from pyarchrules.core.rules.rule import Rule
from pyarchrules.model.rules.rule_violation import RuleViolation


class ImportBaseRule(Rule):
    """Base rule that iterates over ``.py`` files, parses imports, and delegates checking.

    Subclasses implement :meth:`_check_file` to produce violations for a single file.

    Parameters
    ----------
    service_spec : ServiceSpec
        Specification of the service being validated.
    folder : str, optional
        Sub-path relative to the service root to restrict scanning to.
        When ``None`` the entire service directory is scanned.
    """

    def __init__(self, service_spec, folder: str | None = None):
        super().__init__(service_spec)
        self._folder = folder

    # ------------------------------------------------------------------
    # Public Rule interface
    # ------------------------------------------------------------------

    def validate(self) -> list[RuleViolation]:
        """Scan all ``.py`` files and collect import violations.

        Returns
        -------
        list[RuleViolation]
            A single error if the scan root does not exist, otherwise all
            violations returned by :meth:`_check_file` for each file.
        """
        scan_root = self._resolve_scan_root()
        if not scan_root.exists():
            return [
                RuleViolation(
                    rule_name=self.rule_name,
                    service_name=self._service_spec.name,
                    severity="error",
                    message=f"Directory does not exist: "
                    f"{scan_root.relative_to(self._service_spec.project_root)}",
                )
            ]

        violations: list[RuleViolation] = []
        for py_file in sorted(scan_root.rglob("*.py")):
            if "__pycache__" in py_file.parts:
                continue
            imports = collect_imports(py_file)
            rel_path = py_file.relative_to(self._service_spec.absolute_path)
            violations.extend(self._check_file(py_file, rel_path, imports))

        return violations

    # ------------------------------------------------------------------
    # Hook for subclasses
    # ------------------------------------------------------------------

    @abstractmethod
    def _check_file(
        self,
        file: Path,
        rel_path: Path,
        imports: list[ImportInfo],
    ) -> list[RuleViolation]:
        """Inspect one file and return any violations.

        Parameters
        ----------
        file : Path
            Absolute path to the ``.py`` file.
        rel_path : Path
            Path relative to the service root, used in violation messages.
        imports : list[ImportInfo]
            Parsed import statements from the file.

        Returns
        -------
        list[RuleViolation]
        """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_scan_root(self) -> Path:
        """Return the directory that will be scanned recursively.

        Returns
        -------
        Path
            ``service_root / folder`` when *folder* was supplied,
            otherwise the service root itself.
        """
        base = self._service_spec.absolute_path
        return base / self._folder if self._folder else base

    def _make_violation(
        self, rel_path: Path, message: str, severity: str = "error", details: dict | None = None
    ) -> RuleViolation:
        """Build a :class:`~pyarchrules.model.rules.rule_violation.RuleViolation` for a file.

        Parameters
        ----------
        rel_path : Path
            File path relative to the service root, prepended to *message*.
        message : str
            Human-readable description of what went wrong.
        severity : str, optional
            ``"error"`` (default) or ``"warning"``.
        details : dict, optional
            Extra context attached to the violation.

        Returns
        -------
        RuleViolation
        """
        return RuleViolation(
            rule_name=self.rule_name,
            service_name=self._service_spec.name,
            severity=severity,  # type: ignore[arg-type]
            message=f"{rel_path}: {message}",
            details=details or {},
        )
