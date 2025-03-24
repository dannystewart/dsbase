from __future__ import annotations

import types
from collections.abc import Iterable
from typing import Literal

# Type alias for exception info tuple
type ExcInfo = tuple[type[BaseException], BaseException, types.TracebackType | None]

# Translation table for smart quotes replacement
SMART_QUOTES_TABLE = str.maketrans({
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
})

# Color names for termcolor
ColorName = Literal[
    "black",
    "grey",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "light_grey",
    "dark_grey",
    "light_red",
    "light_green",
    "light_yellow",
    "light_blue",
    "light_magenta",
    "light_cyan",
    "white",
]

# Color attributes for termcolor
ColorAttrs = Iterable[
    Literal[
        "bold",
        "dark",
        "underline",
        "blink",
        "reverse",
        "concealed",
    ]
]

# Mapping of text attributes for Rich
rich_attrs: dict[str, str] = {
    "bold": "bold",
    "dark": "dim",
    "underline": "underline",
    "blink": "blink",
    "reverse": "reverse",
    "concealed": "hidden",
}
