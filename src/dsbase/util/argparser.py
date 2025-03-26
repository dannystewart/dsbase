from __future__ import annotations

import argparse
import re
from typing import Any, ClassVar

from dsbase.util.setup import get_caller_package_name, get_version_info


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

    DEFAULT_MAX_WIDTH: ClassVar[int] = 100
    DEFAULT_MIN_ARG_WIDTH: ClassVar[int] = 20
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
        self.version_flags = kwargs.pop("version_flags", ["-v", "--version"])

        # Extract the lines parameter (0 means all lines)
        self.description_lines = kwargs.pop("lines", 0)

        # Process description if it exists
        if "description" in kwargs and kwargs["description"] is not None:
            kwargs["description"] = self._format_description_text(
                kwargs["description"], self.description_lines
            )

        # Use fixed width if provided, otherwise use min_arg_width as starting point
        help_position = self.arg_width if self.arg_width != "auto" else self.min_arg_width

        # Define formatter_class to create our custom formatter
        def create_formatter(prog: str) -> argparse.HelpFormatter:
            formatter = CustomHelpFormatter(
                prog, max_help_position=help_position, width=self.max_width
            )
            formatter.parser = self
            return formatter

        kwargs["formatter_class"] = create_formatter

        super().__init__(*args, **kwargs)

        # Add version argument if requested
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
        package_name = get_caller_package_name()
        version_info = get_version_info(package_name)

        version_string = str(version_info)
        self.add_argument(*self.version_flags, action="version", version=version_string)

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

    def print_help(self, file: Any = None) -> None:
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

        # Add padding first, then clamp to min/max range
        optimal_width = max_length + self.padding
        optimal_width = min(self.max_arg_width, max(self.min_arg_width, optimal_width))

        # Create a formatter factory that uses prog
        self._formatter_class = lambda prog: CustomHelpFormatter(
            prog, max_help_position=optimal_width, width=self.max_width
        )

        # Make sure each formatter gets a reference to the parser
        original_get_formatter = self._get_formatter

        def get_formatter() -> argparse.HelpFormatter:
            formatter = original_get_formatter()
            if isinstance(formatter, CustomHelpFormatter):
                custom_formatter = formatter
                custom_formatter.parser = self
            return formatter

        self._get_formatter = get_formatter


class CustomHelpFormatter(argparse.HelpFormatter):
    """Format a help message for argparse.

    This help formatter allows for customizing the column widths of arguments and help text in an
    argument parser. You can use it by passing it as the formatter_class to ArgumentParser, but it's
    designed for the custom ArgParser class and not intended to be used directly.
    """

    def __init__(self, prog: str, max_help_position: int = 24, width: int = 120):
        super().__init__(prog, max_help_position=max_help_position, width=width)
        self.custom_max_help_position = max_help_position
        self.custom_width = width
        self._parser: ArgParser | None = None

    @property
    def parser(self) -> ArgParser | None:
        """Get the associated ArgParser instance."""
        return self._parser

    @parser.setter
    def parser(self, value: ArgParser) -> None:
        """Set the associated ArgParser instance."""
        self._parser = value

    def _format_action(self, action: argparse.Action) -> str:
        # Calculate the action string (flags and metavar)
        action_header = self._format_action_invocation(action)

        # Determine the indentation of help text
        indent = " " * self._current_indent

        # Parts will store the lines of our formatted action
        parts = [indent + action_header]

        # If there's no help text, just return the action header
        if not action.help:
            parts.append("\n")
            return "".join(parts)

        # Get parser settings or use defaults
        min_arg_width = 20  # Default value
        max_arg_width = 40  # Default value
        padding = 2  # Default padding

        if self._parser:
            if hasattr(self._parser, "min_arg_width"):
                min_arg_width = self._parser.min_arg_width
            if hasattr(self._parser, "max_arg_width"):
                max_arg_width = self._parser.max_arg_width
            if hasattr(self._parser, "padding"):
                padding = self._parser.padding

        # Calculate help position based on argument length plus padding
        action_length = len(indent) + len(action_header)

        # Calculate help position, respecting min_arg_width and max_arg_width
        help_position = max(min_arg_width, action_length + padding)
        help_position = min(max_arg_width, help_position)

        help_indent = " " * help_position

        # If header and padding exceed calculated help position, move to next line
        if action_length + padding > help_position:
            parts.extend(("\n", help_indent))
        else:  # Add padding spaces
            padding_spaces = help_position - action_length
            parts.append(" " * padding_spaces)

        # Add the help text, properly wrapped
        help_lines = self._split_lines(action.help, self.custom_width - help_position)
        parts.append(help_lines[0])

        # If there are additional help lines, add them with proper indentation
        for line in help_lines[1:]:
            parts.extend(("\n", help_indent, line))

        # Add a final newline
        parts.append("\n")

        return "".join(parts)
