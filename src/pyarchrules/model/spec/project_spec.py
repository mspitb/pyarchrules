"""Project specification model."""

from __future__ import annotations

from pydantic import BaseModel, Field

from pyarchrules.model.spec.service_spec import ServiceSpec


class ProjectSpec(BaseModel):
    """Project configuration specification."""

    validate_paths: bool = True
    isolate_services: bool = False
    services: dict[str, ServiceSpec] = Field(default_factory=dict)
