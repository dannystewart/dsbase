from __future__ import annotations

from .color import info, progress
from .text import Text
from .types import ColorAttrs, ColorName

color = Text.color
color_print = Text.color_print

# For backward compatibility
print_colored = Text.color_print
