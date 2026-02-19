from loguru import logger

from pyarchrules.core.registries import DSLRegistry, LinterRegistry
from pyarchrules.model.spec import ProjectSpec, ServiceSpec
from pyarchrules.pyarchrules import PyArchRules

# Configure loguru for clean output (like isort/ruff) - no timestamps, no extra info
logger.remove()  # Remove default handler
logger.add(
    lambda msg: print(msg, end=""),
    format="{message}\n",
    level="INFO",
    colorize=True,
)

__all__ = [
    "PyArchRules",
    "ProjectSpec",
    "ServiceSpec",
    "DSLRegistry",
    "LinterRegistry",
]
