"""Parsed ``source -> target`` dependency rule."""

from __future__ import annotations

from dataclasses import dataclass

from pyarchrules.core.errors import ConfigError


@dataclass(slots=True, frozen=True)
class DependencyRule:
    """One ``"source -> target"`` entry of ``ServiceSpec.dependencies``.

    ``source`` and ``target`` are POSIX paths relative to the service root
    (or ``"*"``); ``original`` is the string exactly as the user wrote it.
    """

    source: str
    target: str
    original: str

    @classmethod
    def parse(cls, raw: str) -> DependencyRule:
        """Parse a single rule string.

        Raises
        ------
        ConfigError
            On a wrong arrow, empty side, ``* -> *`` or an unsafe path.
        """
        text = raw.strip()

        if "<-" in text:
            raise ConfigError(
                "invalid arrow '<-'. Use '->' (e.g., 'api -> domain' means api can use domain)"
            )
        if "->" not in text:
            raise ConfigError("missing '->'. Example: 'api -> domain' means api can use domain")

        source, target = (side.strip() for side in text.split("->", 1))
        if not source or not target:
            raise ConfigError("empty source or target")
        if source == "*" and target == "*":
            raise ConfigError("'* -> *' is not allowed — it would permit everything")

        for path in (source, target):
            if path != "*" and (path.startswith(("/", "\\")) or ".." in path):
                raise ConfigError(f"invalid path: {path}")

        return cls(_normalize(source), _normalize(target), raw)


def _normalize(path: str) -> str:
    return path if path == "*" else path.replace("\\", "/").strip("/")
