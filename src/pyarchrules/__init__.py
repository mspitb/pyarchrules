import sys

from loguru import logger

from pyarchrules.core.registries import DSLRegistry, LinterRegistry
from pyarchrules.model.spec import ProjectSpec, ServiceSpec
from pyarchrules.pyarchrules import PyArchRules

logger.remove()
logger.add(sys.stderr, format="{message}\n", level="INFO", colorize=True)

__all__ = [
    "PyArchRules",
    "ProjectSpec",
    "ServiceSpec",
    "DSLRegistry",
    "LinterRegistry",
]
