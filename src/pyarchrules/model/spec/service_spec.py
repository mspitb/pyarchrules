"""Service specification model."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from pyarchrules.model.spec.tree_node_spec import TreeNodeSpec


class ServiceSpec(BaseModel):
    """Specification for a service."""

    name: str
    path: str
    project_root: Path
    allowed_service_dependencies: list[str] = Field(default_factory=list)
    tree: dict[str, TreeNodeSpec] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}

    @property
    def absolute_path(self) -> Path:
        return self.project_root / self.path
