"""Finding model for lint results."""

from typing import NamedTuple


class Finding(NamedTuple):
    """A single lint finding (error or warning)."""
    check: str
    severity: str  # "error" or "warning"
    message: str

    def __repr__(self) -> str:
        return f"[{self.severity}] {self.check}: {self.message}"
