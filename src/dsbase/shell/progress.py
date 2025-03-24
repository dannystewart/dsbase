"""Utilities for displaying progress messages and spinners."""

from __future__ import annotations

from contextlib import contextmanager
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar

from halo import Halo

from dsbase.text import ColorName, print_colored
from dsbase.text import color as colorize

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from pathlib import Path

T = TypeVar("T")


def with_spinner(
    text: str = "Processing...",
    success: str | None = None,
    color: ColorName = "cyan",
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Display a spinner while the decorated function is running.

    Args:
        text: The text to display before the spinner. Defaults to "Processing...".
        success: The text to display when the function completes successfully. Defaults to "Done!".
        color: The color of the text. Defaults to 'cyan'.
    """

    def spinner_decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            spinner_text = colorize(text, color) if color else text
            spinner = Halo(text=spinner_text, spinner="dots", color=color)
            spinner.start()
            try:
                result = func(*args, **kwargs)
                if success:
                    spinner.succeed(colorize(success, color))
                else:
                    spinner.stop()
            except Exception as e:
                spinner.fail(colorize(f"Failed: {e}", "red"))
                raise
            finally:
                spinner.stop()
            return result

        return wrapper

    return spinner_decorator


@contextmanager
def halo_progress(
    item: str | Path | None = None,
    start_message: str = "Processing",
    end_message: str = "Processed",
    fail_message: str = "Failed",
    text_color: ColorName = "cyan",
    success_color: ColorName = "green",
    fail_color: ColorName = "red",
    show: bool = True,
) -> Generator[Halo | None, None, None]:
    """Context manager to display a Halo spinner while a block of code is executing, with customized
    start and end messages.

    Args:
        item: The name of the item being processed. Accepts string or Path.
        start_message: The start message to display.
        end_message: The end message to display.
        fail_message: The fail message to display.
        text_color: The color of the spinner text. Defaults to 'cyan'.
        success_color: The color of the success message. Defaults to 'green'.
        fail_color: The color of the fail message. Defaults to 'red'.
        show: Whether to show the Halo spinner output. Defaults to True.

    Usage:
        file_path = "example.txt"
        with halo_progress(file_path) as spinner:
            process_file(file_path)

        You can use spinner.succeed() or spinner.fail() to update the spinner status.

    Yields:
        Halo: The Halo spinner.
    """
    if item:
        start_message = f"{start_message} {item}"
        end_message = f"{end_message} {item}"
        fail_message = f"{fail_message} {item}"

    if show:
        spinner = Halo(text=colorize(start_message, text_color), spinner="dots")
        spinner.start()
    else:
        spinner = None

    try:
        yield spinner
    except Exception as e:
        if spinner is not None and show:
            spinner.fail(colorize(f"{fail_message}: {e}", fail_color))
        else:
            print_colored(f"{fail_message}: {e}", fail_color)
        raise
    if spinner and show:
        spinner.succeed(colorize(end_message, success_color))
    elif show:
        print_colored(end_message, success_color)


@contextmanager
def conversion_list_context(file_name: str) -> Generator[None, None, None]:
    """Context manager to print a message at the start and end of an operation.

    Args:
        file_name: The name of the file being converted.
    """
    try:
        print(f"Converting {file_name} ... ", end="")
        yield
    finally:
        print(colorize("done!", "green"))
