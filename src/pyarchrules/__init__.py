"""PyArchRules — architecture validation for Python projects."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from pyarchrules.core.errors import (
    ConfigError,
    PyArchError,
    ServiceNotFoundError,
    ValidationError,
)
from pyarchrules.model.rules import RuleEvalResult, RuleViolation
from pyarchrules.model.spec import ProjectSpec, ServiceSpec
from pyarchrules.pyarchrules import PyArchRules

try:
    __version__ = _pkg_version("pyarchrules")
except PackageNotFoundError:  # pragma: no cover - running from a checkout without install
    __version__ = "0.0.0+local"

__all__ = [
    "ConfigError",
    "ProjectSpec",
    "PyArchError",
    "PyArchRules",
    "RuleEvalResult",
    "RuleViolation",
    "ServiceNotFoundError",
    "ServiceSpec",
    "ValidationError",
    "__version__",
]
