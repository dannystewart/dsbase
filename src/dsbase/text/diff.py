from __future__ import annotations

from dataclasses import dataclass
from difflib import unified_diff
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from dsbase import LocalLogger

if TYPE_CHECKING:
    from logging import Logger


@dataclass
class DiffResult:
    """Result of a diff comparison."""

    has_changes: bool
    changes: list[str]
    additions: list[str]
    deletions: list[str]


class DiffStyle(StrEnum):
    """Style of diff output."""

    COLORED = "colored"
    SIMPLE = "simple"
    MINIMAL = "minimal"


def diff_files(
    old_path: str | Path,
    new_path: str | Path,
    style: DiffStyle = DiffStyle.COLORED,
) -> DiffResult:
    """Show diff between two files.

    Args:
        old_path: The original file to be compared against the new file.
        new_path: The new file which, if different, would overwrite the original content.
        style: Styling to use for displaying the diff output. Defaults to colored.

    Returns:
        DiffResult containing the changes found.
    """
    return show_diff(
        old=Path(old_path).read_text(encoding="utf-8"),
        new=Path(new_path).read_text(encoding="utf-8"),
        filename=str(new_path),
        style=style,
    )


def show_diff(
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
        style: The styling to use for displaying the diff output. Defaults to colored.
        logger: An optional external logger to use. Otherwise a local logger is created.

    Returns:
        A DiffResult object containing the changes that were identified.
    """
    logger = logger or LocalLogger().get_logger(simple=True)
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
        if filename or logger:
            logger.info("No changes detected in %s.", content)
        return DiffResult(False, [], [], [])

    if filename:
        logger.info("Changes detected in %s:", content)

    for line in diff:
        changes.append(line.rstrip())
        _process_diff_line(line, style, logger, additions, deletions)

    return DiffResult(True, changes, additions, deletions)


def _process_diff_line(
    line: str,
    style: DiffStyle,
    log_func: Logger,
    additions: list[str],
    deletions: list[str],
) -> None:
    """Process a single line of diff output."""
    if not _should_show_line(line, style):
        return

    if style == DiffStyle.COLORED:
        if line.startswith("+"):
            log_func.info("  %s", line.rstrip())
        elif line.startswith("-"):
            log_func.warning("  %s", line.rstrip())
        else:
            log_func.debug("  %s", line.rstrip())
    else:
        log_func.info("  %s", line.rstrip())

    if line.startswith("+"):
        additions.append(line.rstrip())
    elif line.startswith("-"):
        deletions.append(line.rstrip())


def _should_show_line(line: str, style: DiffStyle) -> bool:
    """Determine if a line should be shown based on the diff style."""
    return style in {DiffStyle.COLORED, DiffStyle.SIMPLE} or (
        style == DiffStyle.MINIMAL and line.startswith(("+", "-"))
    )
