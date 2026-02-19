"""Tree node specification for directory structure."""

from __future__ import annotations

from pydantic import BaseModel


class TreeNodeSpec(BaseModel):
    """Directory node specification.

    Represents a path that must exist in the service directory.
    If allow_extra is False, no additional files/folders are allowed in that path.
    """

    path: str
    allow_extra: bool = True
