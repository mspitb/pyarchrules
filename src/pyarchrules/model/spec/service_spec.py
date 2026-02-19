"""Service specification model."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class ServiceSpec(BaseModel):
    """Specification for a service."""

    name: str
    path: str
    project_root: Path
    allowed_service_dependencies: list[str] = Field(default_factory=list)
    tree: list[str] = Field(default_factory=list)
    tree_strict: bool = False  # If True, no extra files/folders allowed in tree paths
    tree_allow_files: bool = True  # If tree_strict=True, this allows files (but not folders)
    dependencies: list[str] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}

    @property
    def absolute_path(self) -> Path:
        return self.project_root / self.path
