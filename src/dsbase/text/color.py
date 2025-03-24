from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dsbase.text.types import ColorAttrs, ColorName


def color(text: Any, color_name: ColorName, attrs: ColorAttrs | None = None) -> str:
    """Use termcolor to return a string in the specified color if termcolor is available.
    Otherwise, gracefully falls back to returning the text as is.

    Args:
        text: The text to colorize. Can accept non-strings, and will attempt to convert them.
        color_name: The name of the color.
        attrs: A list of attributes to apply to the text (e.g. ['bold', 'underline']).

    Returns:
        The colorized text.
    """
    text = str(text)  # Ensure text is a string

    try:
        from termcolor import colored
    except ImportError:
        return text

    return colored(text, color_name, attrs=attrs)


def print_colored(
    text: Any, color_name: ColorName, end: str = "\n", attrs: ColorAttrs | None = None
) -> None:
    r"""Use termcolor to print text in the specified color if termcolor is available.
    Otherwise, gracefully falls back to printing the text as is.

    Args:
        text: The text to print in color. Can accept non-strings, and will attempt to convert them.
        color_name: The name of the color.
        end: The string to append after the last value. Defaults to "\n".
        attrs: A list of attributes to apply to the text (e.g. ['bold', 'underline']).
    """
    text = str(text)  # Ensure text is a string

    try:
        from termcolor import colored
    except ImportError:
        print(text, end=end)
        return

    print(colored(text, color_name, attrs=attrs), end=end)


def info(message: str) -> None:
    """Print an informational message."""
    print_colored(message, "blue")


def progress(message: str) -> None:
    """Print a success/progress message."""
    print_colored(f"✔ {message}", "green")


def warning(message: str) -> None:
    """Print a warning message."""
    print_colored(message, "yellow")


def error(message: str, skip_exit: bool = False) -> None:
    """Print an error message and exit the program."""
    print_colored(f"\n{message}", "red")
    if not skip_exit:
        sys.exit(1)
