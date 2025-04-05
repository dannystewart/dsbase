from __future__ import annotations

import argparse
import re
import textwrap
from typing import Any, ClassVar

from polykit.packages import VersionChecker


class ArgParser(argparse.ArgumentParser):
    """Drop-in replacement for ArgumentParser with easier adjustment of column widths.

    Args:
        arg_width: The width of the argument column in the help text. Defaults to 'auto',
                   which automatically determines the optimal width based on arguments.
        max_width: The maximum width of the help text.
        min_arg_width: Minimum width for argument column when using 'auto' mode. Note that due to
                       argparse limitations the help text won't begin earlier than column 26.
        max_arg_width: Maximum width for argument column when using 'auto' mode.
        padding: Additional padding to add to the calculated width in 'auto' mode.
        add_version: If True, automatically adds a version argument using polykit.
        version_flags: List of flags to use for the version argument. Defaults to ['--version'].

    Example:
        # to automatically determine the optimal argument width
        parser = ArgParser(description=__doc__)

        # or to set fixed widths
        parser = ArgParser(description=__doc__, arg_width=24, max_width=120)
    """

    DEFAULT_MAX_WIDTH: ClassVar[int] = 100
    DEFAULT_MIN_ARG_WIDTH: ClassVar[int] = 20  # argparse help text won't start lower than column 26
    DEFAULT_MAX_ARG_WIDTH: ClassVar[int] = 40
    DEFAULT_PADDING: ClassVar[int] = 4

    def __init__(self, *args: Any, **kwargs: Any):
        self.arg_width = kwargs.pop("arg_width", "auto")
        self.max_width = kwargs.pop("max_width", self.DEFAULT_MAX_WIDTH)
        self.min_arg_width = kwargs.pop("min_arg_width", self.DEFAULT_MIN_ARG_WIDTH)
        self.max_arg_width = kwargs.pop("max_arg_width", self.DEFAULT_MAX_ARG_WIDTH)
        self.padding = kwargs.pop("padding", self.DEFAULT_PADDING)

        # Version handling options
        self.add_version = kwargs.pop("add_version", True)
        self.version_flags = kwargs.pop("version_flags", ["--version"])

        # Extract the lines parameter (0 means all lines)
        self.description_lines = kwargs.pop("lines", 0)

        # Process description if it exists
        if "description" in kwargs and kwargs["description"] is not None:
            kwargs["description"] = self._format_description_text(
                kwargs["description"], self.description_lines
            )

        # Use fixed width if provided, otherwise use min_arg_width as starting point
        help_position = self.arg_width if self.arg_width != "auto" else self.min_arg_width

        # Set the formatter_class in kwargs
        kwargs["formatter_class"] = lambda prog: CustomHelpFormatter(
            prog, max_help_position=help_position, width=self.max_width
        )

        super().__init__(*args, **kwargs)

        # Add --version argument if requested and dsbin is available
        if self.add_version:
            self._add_version_argument()

    def add_argument(self, *args: Any, **kwargs: Any) -> argparse.Action:
        """Override add_argument to automatically lowercase help text."""
        # Extract the keep_caps parameter, defaulting to False
        keep_caps = kwargs.pop("keep_caps", False)

        # Process the help text if it exists and keep_caps is False
        if "help" in kwargs and kwargs["help"] and not keep_caps:
            help_text = kwargs["help"]
            # Only lowercase the first character, preserving the rest
            if help_text and len(help_text) > 0:
                kwargs["help"] = help_text[0].lower() + help_text[1:]

        # Call the argparser's add_argument method
        return super().add_argument(*args, **kwargs)

    def _add_version_argument(self) -> None:
        """Add a version argument that automatically detects package version."""
        # Get the package name from the script name
        package_name = VersionChecker.get_caller_package_name()

        # Use the VersionChecker to get comprehensive version info
        checker = VersionChecker()
        version_info = checker.check_package(package_name)

        # Add the version argument
        self.add_argument(*self.version_flags, action="version", version=str(version_info))

    def _format_description_text(self, text: str, lines: int = 0) -> str:
        """Prepare description text by preserving paragraph structure.

        Args:
            text: The text to format.
            lines: Number of paragraphs to include (0 means all).
        """
        # Remove leading/trailing whitespace and normalize line breaks
        text = text.strip().replace("\r\n", "\n")

        # Replace single line breaks with spaces (within paragraphs)
        # But preserve paragraph breaks (double line breaks)
        text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

        # Normalize multiple consecutive line breaks to exactly two
        text = re.sub(r"\n{2,}", "\n\n", text)

        # If lines is specified, limit to that number of paragraphs
        if lines > 0:
            paragraphs = text.split("\n\n")
            text = "\n\n".join(paragraphs[:lines])

        return text

    def format_help(self) -> str:
        """Override format_help to update formatter before generating help text."""
        if self.arg_width == "auto":
            self._update_formatter()
        return super().format_help()

    def print_help(self, file: Any | None = None) -> None:
        """Override print_help to update formatter before printing help text."""
        if self.arg_width == "auto":
            self._update_formatter()
        return super().print_help(file)

    def _update_formatter(self) -> None:
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
            if action.metavar is not None:
                metavar_str = action.metavar
                if isinstance(metavar_str, tuple):
                    metavar_str = " ".join(metavar_str)
                if action.option_strings:
                    length += len(metavar_str) + 1  # +1 for space
            elif action.dest != argparse.SUPPRESS and action.nargs != 0:
                length += len(action.dest) + 1

            max_length = max(max_length, length)

        # First, clamp the argument width to min/max range, then add padding
        arg_width = min(self.max_arg_width, max(self.min_arg_width, max_length))
        help_position = arg_width + self.padding

        # Create a new formatter with the calculated width
        self._formatter_class = lambda prog: CustomHelpFormatter(
            prog, max_help_position=help_position, width=self.max_width
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

    def _format_text(self, text: str) -> str:
        """Override to handle paragraph breaks in description and epilog text."""
        # Split text into paragraphs
        paragraphs = text.split("\n\n")
        result = []

        # Process each paragraph with textwrap
        for paragraph in paragraphs:
            # Wrap each paragraph to the appropriate width
            wrapped = textwrap.fill(paragraph, self._width)
            result.append(wrapped)

        # Join paragraphs with double newlines and add a newline at the end
        return "\n\n".join(result) + "\n"

    def _split_lines(self, text: str, width: int) -> list[str]:
        return textwrap.wrap(text, width)

    def _format_action(self, action: argparse.Action) -> str:
        # Get the formatted action from the parent class
        parts = super()._format_action(action)

        if action.help:  # If there's help text, ensure proper spacing
            help_position = parts.find(action.help)
            if help_position > 0:  # Only adjust if we found the help text
                space_to_insert = max(self.custom_max_help_position - help_position, 0)
                parts = parts[:help_position] + (" " * space_to_insert) + parts[help_position:]
        return parts
