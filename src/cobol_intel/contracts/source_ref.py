"""SourceRef — reusable model for pointing back to source locations.

Shared layer candidate (suite-friendly): every future module that produces
findings needs to point back to a source. Keep this generic.
"""

from __future__ import annotations

from pydantic import BaseModel


class SourceRef(BaseModel):
    """Points to a location in a source file."""

    file: str
    paragraph: str | None = None
    lines: tuple[int, int] | None = None
    module: str | None = None
