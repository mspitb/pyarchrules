"""Project specification model."""

from __future__ import annotations

from dataclasses import dataclass, field

from pyarchrules.model.spec.service_spec import ServiceSpec


@dataclass(slots=True, frozen=True)
class ProjectSpec:
    """Project configuration specification.

    Attributes
    ----------
    services : dict[str, ServiceSpec]
        Mapping of service name to its specification.
    isolate_services : bool
        When ``True``, every non-``shared`` service is forbidden from
        importing the internals of other services in this project.
        Configured via ``isolate_services = true`` in ``[tool.pyarchrules]``.
    """

    services: dict[str, ServiceSpec] = field(default_factory=dict)
    isolate_services: bool = False
