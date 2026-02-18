"""Project specification model."""

from __future__ import annotations

from pydantic import BaseModel, Field

from pyarchrules.model.spec.service_spec import ServiceSpec


class ProjectSpec(BaseModel):
    """Project configuration specification."""

    strict: bool = True
    validate_paths: bool = True
    services: dict[str, ServiceSpec] = Field(default_factory=dict)
