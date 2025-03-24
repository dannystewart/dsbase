from __future__ import annotations

import argparse
import textwrap
from typing import Any


class ArgParser(argparse.ArgumentParser):
    """Drop-in replacement for ArgumentParser with easier adjustment of column widths.

    Args:
        arg_width: The width of the argument column in the help text. Defaults to 'auto',
                   which automatically determines the optimal width based on arguments.
        max_width: The maximum width of the help text.
        min_arg_width: Minimum width for argument column when using 'auto' mode.
        max_arg_width: Maximum width for argument column when using 'auto' mode.
        padding: Additional padding to add to the calculated width in 'auto' mode.

    Example:
        # to automatically determine the optimal argument width
        parser = ArgParser(description=__doc__)

        # or to set fixed widths
        parser = ArgParser(description=__doc__, arg_width=24, max_width=120)
    """

    def __init__(self, *args: Any, **kwargs: Any):
        self.arg_width = kwargs.pop("arg_width", "auto")
        self.max_width = kwargs.pop("max_width", 120)
        self.min_arg_width = kwargs.pop("min_arg_width", 15)
        self.max_arg_width = kwargs.pop("max_arg_width", 35)
        self.padding = kwargs.pop("padding", 4)

        # Initialize with a temporary formatter
        super().__init__(
            *args,
            **kwargs,
            formatter_class=lambda prog: CustomHelpFormatter(
                prog, max_help_position=self.min_arg_width, width=self.max_width
            ),
        )

    def add_argument(self, *args: Any, **kwargs: Any) -> argparse.Action:
        """Override add_argument to track all arguments for auto-width calculation."""
        return super().add_argument(*args, **kwargs)

    def format_help(self) -> str:
        """Override format_help to update formatter before generating help text."""
        if self.arg_width == "auto":
            self._update_formatter()
        return super().format_help()

    def print_help(self, file: Any = None) -> None:
        """Override print_help to update formatter before printing help text."""
        if self.arg_width == "auto":
            self._update_formatter()
        return super().print_help(file)

    def _update_formatter(self):
        """Calculate the optimal argument width based on current arguments."""
        if not self._actions:
            return

        # Calculate the width needed for the longest argument
        max_length = 0
        for action in self._actions:
            # Calculate the length of the argument representation
            length = 0
            if action.option_strings:
                length = max(len(", ".join(action.option_strings)), length)
            elif action.dest != argparse.SUPPRESS:
                length = max(len(action.dest), length)

            # Account for metavar if present
            if action.metavar:
                metavar_str = action.metavar
                if isinstance(metavar_str, tuple):
                    metavar_str = " ".join(metavar_str)
                if action.option_strings:
                    length += len(metavar_str) + 1  # +1 for space
            elif action.dest != argparse.SUPPRESS and action.nargs != 0:
                length += len(action.dest) + 1

            max_length = max(max_length, length)

        # Add padding and clamp to min/max
        optimal_width = min(self.max_arg_width, max(self.min_arg_width, max_length + self.padding))

        # Update the formatter class
        self.formatter_class = lambda prog: CustomHelpFormatter(
            prog, max_help_position=optimal_width, width=self.max_width
        )


class CustomHelpFormatter(argparse.HelpFormatter):
    """Format a help message for argparse.

    This help formatter allows for customizing the column widths of arguments and help text in an
    argument parser. You can use it by passing it as the formatter_class to ArgumentParser, but it's
    designed for the custom ArgParser class and not intended to be used directly.
    """

    def __init__(self, prog: str, max_help_position: int = 24, width: int = 120):
        super().__init__(prog, max_help_position=max_help_position, width=width)
        self.custom_max_help_position = max_help_position

    def _split_lines(self, text: str, width: int) -> list[str]:
        return textwrap.wrap(text, width)

    def _format_action(self, action: argparse.Action) -> str:
        parts = super()._format_action(action)
        if action.help:
            help_position = parts.find(action.help)
            space_to_insert = max(self.custom_max_help_position - help_position, 0)
            parts = parts[:help_position] + (" " * space_to_insert) + parts[help_position:]
        return parts
