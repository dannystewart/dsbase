from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from natsort import natsorted

from dsbase.text import print_colored
from dsbase.time import TZ

if TYPE_CHECKING:
    from collections.abc import Callable


def list_files(
    dir: str | Path,  # noqa: A002
    exts: str | list[str] | None = None,
    recursive: bool = False,
    min_size: int | None = None,
    max_size: int | None = None,
    exclude: str | list[str] | None = None,
    include_hidden: bool = False,
    modified_after: datetime | None = None,
    modified_before: datetime | None = None,
    sort_key: Callable[..., Any] | None = None,
    reverse_sort: bool = False,
) -> list[Path]:
    """List all files in a directory that match the given criteria.

    Args:
        dir: The directory to search.
        exts: The file extensions to include. If None, all files will be included.
        recursive: Whether to search recursively.
        min_size: The minimum file size in bytes.
        max_size: The maximum file size in bytes.
        exclude: Glob patterns to exclude.
        include_hidden: Whether to include hidden files.
        modified_after: Only include files modified after this date.
        modified_before: Only include files modified before this date.
        sort_key: A function to use for sorting the files.
        reverse_sort: Whether to reverse the sort order.

    Returns:
        A list of file paths as Path objects.

    Example usage with custom sort (alphabetical sorting by file name):
        `file_list = list_files(dir, sort_key=lambda x: x.stat().st_mtime)`

    Notes:
        - The `exts` parameter should not include the dot prefix (e.g. 'txt' not '.txt').
        - The `modified_after` and `modified_before` expect datetime.datetime objects.
        - Sorting is performed by modification time in ascending order by default. Customize sorting
            with the 'sort_key' and 'reverse' parameters.
    """
    dir_path = Path(dir)
    if exts:
        exts = [ex.lstrip(".") for ex in (exts if isinstance(exts, list) else [exts])]
        exts = [f"*.{ext}" for ext in exts]
    else:
        exts = ["*"]
    files_filtered: list[Path] = []
    for ext in exts:
        files = dir_path.rglob(ext) if recursive else dir_path.glob(ext)
        files_filtered.extend(
            file
            for file in files
            if file.is_file()
            and file_matches_criteria(
                file, min_size, max_size, exclude, include_hidden, modified_after, modified_before
            )
        )
    sort_function = sort_key or (lambda x: x.stat().st_mtime)
    return natsorted(files_filtered, key=sort_function, reverse=reverse_sort)


def file_matches_criteria(
    file_path: Path,
    min_size: int | None = None,
    max_size: int | None = None,
    exclude_patterns: str | list[str] | None = None,
    include_hidden: bool = False,
    modified_after: datetime | None = None,
    modified_before: datetime | None = None,
) -> bool:
    """Check if a file matches the given criteria."""
    result = True
    try:
        if (not include_hidden and file_path.name.startswith(".")) or (
            exclude_patterns and any(file_path.match(pattern) for pattern in exclude_patterns)
        ):
            result = False
        else:
            file_stats = file_path.stat()
            file_mtime = datetime.fromtimestamp(file_stats.st_mtime, tz=TZ)
            is_below_min_size = min_size is not None and file_stats.st_size < min_size
            is_above_max_size = max_size is not None and file_stats.st_size > max_size
            is_modified_too_early = modified_after is not None and file_mtime <= modified_after
            is_modified_too_late = modified_before is not None and file_mtime >= modified_before

            if (
                is_below_min_size
                or is_above_max_size
                or is_modified_too_early
                or is_modified_too_late
            ):
                result = False
    except FileNotFoundError:
        print_colored(f"Error accessing file {file_path}: File not found", "red")
        result = False
    return result
