from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class PolyVar:
    """Represents an environment variable with validation and type conversion.

    Args:
        name: Environment variable name.
        required: Whether this variable is required.
        default: Default value if not required.
        var_type: Type to convert value to (e.g., int, float, str, bool).
        description: Human-readable description of the variable.
        secret: Whether to mask the value in logs.

    NOTE: var_type is used as a converter function to wrap the provided data. This means it can also
          use custom conversion functions to get other types of data with convert(value) -> Any.
    """

    name: str
    required: bool = False
    default: Any = None
    var_type: Callable[[str], Any] = str
    description: str = ""
    secret: bool = False

    def __post_init__(self) -> None:
        if not self.required and self.default is None:
            msg = f"Non-required variable {self.name} must have a default value"
            raise ValueError(msg)
