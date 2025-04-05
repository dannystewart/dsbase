from __future__ import annotations

from difflib import unified_diff
from pathlib import Path
from typing import TYPE_CHECKING

from polykit.files.types import DiffResult, DiffStyle
from polykit.log import PolyLog

if TYPE_CHECKING:
    from logging import Logger


class PolyDiff:
    """A utility class with a set of methods to compare files and show differences."""

    @classmethod
    def files(
        cls,
        old_path: str | Path,
        new_path: str | Path,
        style: DiffStyle = DiffStyle.COLORED,
        logger: Logger | None = None,
    ) -> DiffResult:
        """Show diff between two files.

        Args:
            old_path: The original file to be compared against the new file.
            new_path: The new file which, if different, would overwrite the original content.
            style: The styling to use for the diff output. Defaults to colored.
            logger: Optional logger for operation information.

        Returns:
            DiffResult containing the changes found.
        """
        return cls.content(
            old=Path(old_path).read_text(encoding="utf-8"),
            new=Path(new_path).read_text(encoding="utf-8"),
            filename=str(new_path),
            style=style,
            logger=logger,
        )

    @classmethod
    def content(
        cls,
        old: str,
        new: str,
        filename: str | None = None,
        *,
        style: DiffStyle = DiffStyle.COLORED,
        logger: Logger | None = None,
    ) -> DiffResult:
        """Show a unified diff between old and new content.

        Args:
            old: The original content to be compared against the new content.
            new: The new content which, if different, would overwrite the original content.
            filename: An optional filename to include in log messages for context.
            style: The styling to use for the diff output. Defaults to colored.
            logger: Optional logger for operation information.

        Returns:
            A DiffResult object containing the changes that were identified.
        """
        # Create a logger only if we need to display output
        temp_logger = None
        if logger is None and style != DiffStyle.MINIMAL:
            temp_logger = PolyLog.get_logger(simple=True)

        log_func = logger or temp_logger
        content = filename or "text"

        changes: list[str] = []
        additions: list[str] = []
        deletions: list[str] = []

        diff = list(
            unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile=f"current {content}" if filename else "current",
                tofile=f"new {content}" if filename else "new",
            )
        )

        if not diff:
            if log_func and filename:
                log_func.info("No changes detected in %s.", content)
            return DiffResult(False, [], [], [])

        if log_func and filename:
            log_func.info("Changes detected in %s:", content)

        for line in diff:
            changes.append(line.rstrip())
            if log_func:
                cls._process_diff_line(line, style, log_func, additions, deletions)
            else:
                # Still track additions and deletions even without logging
                normalized_line = cls._normalize_diff_line(line)
                if line.startswith("+"):
                    additions.append(normalized_line)
                elif line.startswith("-"):
                    deletions.append(normalized_line)

        return DiffResult(True, changes, additions, deletions)

    @classmethod
    def _process_diff_line(
        cls,
        line: str,
        style: DiffStyle,
        log_func: Logger,
        additions: list[str],
        deletions: list[str],
    ) -> None:
        """Process a single line of diff output."""
        if not cls._should_show_line(line, style):
            return

        # Log with normalized spacing
        normalized_line = cls._normalize_diff_line(line)
        if style == DiffStyle.COLORED:
            if line.startswith("+"):
                log_func.info("  %s", normalized_line)
            elif line.startswith("-"):
                log_func.warning("  %s", normalized_line)
            else:
                log_func.debug("  %s", line.rstrip())
        else:
            log_func.info("  %s", normalized_line if line.startswith(("+", "-")) else line.rstrip())

        if line.startswith("+"):
            additions.append(normalized_line)
        elif line.startswith("-"):
            deletions.append(normalized_line)

    @classmethod
    def _normalize_diff_line(cls, line: str) -> str:
        """Normalize a diff line by adding one additional space after the diff marker."""
        # Normalize spacing only between the prefix and content
        if line.startswith(("+", "-")):
            prefix = line[0]
            if len(line) > 1:
                if line[1] == " " and (len(line) == 2 or line[2] != " "):
                    # Already has exactly one space, keep as is
                    normalized_line = line.rstrip()
                elif line[1] == " ":
                    # Has multiple spaces after prefix, normalize to one space
                    normalized_line = prefix + " " + line[2:].rstrip()
                else:
                    # No space after prefix, add one
                    normalized_line = prefix + " " + line[1:].rstrip()
            else:
                normalized_line = prefix + " "  # Just the prefix, add a space
        else:
            normalized_line = line.rstrip()

        return normalized_line

    @classmethod
    def _should_show_line(cls, line: str, style: DiffStyle) -> bool:
        """Determine if a line should be shown based on the diff style."""
        is_colored_or_simple = style in {DiffStyle.COLORED, DiffStyle.SIMPLE}
        is_minimal = style == DiffStyle.MINIMAL
        is_diff_marker = line.startswith(("+", "-", "@"))
        return is_colored_or_simple or (is_minimal and is_diff_marker)
