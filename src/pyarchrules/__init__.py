"""PyArchRules — architecture validation for Python projects."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from pyarchrules.core.registries import DSLRegistry, LinterRegistry
from pyarchrules.model.spec import ProjectSpec, ServiceSpec
from pyarchrules.pyarchrules import PyArchRules

try:
    __version__ = _pkg_version("pyarchrules")
except PackageNotFoundError:  # pragma: no cover — running from a checkout w/o install
    __version__ = "0.0.0+local"

__all__ = [
    "PyArchRules",
    "ProjectSpec",
    "ServiceSpec",
    "DSLRegistry",
    "LinterRegistry",
    "__version__",
]
