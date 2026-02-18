"""Tree node specification for directory structure."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TreeNodeSpec(BaseModel):
    """Directory node specification."""

    subdirs: list[str] = Field(default_factory=list)
    allow_extra: bool = True
