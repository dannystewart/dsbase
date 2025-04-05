from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DiffStyle(StrEnum):
    """Style of diff output."""

    COLORED = "colored"
    SIMPLE = "simple"
    MINIMAL = "minimal"


@dataclass
class DiffResult:
    """Result of a diff comparison."""

    has_changes: bool
    changes: list[str]
    additions: list[str]
    deletions: list[str]
