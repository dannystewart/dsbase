# pylint: disable=too-many-branches
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from dsbase.text import print_colored


def copy_file(
    source: str | Path,
    destination: str | Path,
    overwrite: bool = True,
    show_output: bool = True,
) -> bool:
    """Copy a file from source to destination.

    Args:
        source: The source file path.
        destination: The destination file path.
        overwrite: Whether to overwrite the destination file if it already exists.
        show_output: Whether to print output.
    """
    try:
        source = Path(source)
        destination = Path(destination)

        if not overwrite and destination.exists():
            if show_output:
                print_colored(
                    f"Error: Destination file {destination} already exists. Use overwrite=True to overwrite it.",
                    "yellow",
                )
            return False

        if sys.platform == "win32":
            _copy_win32_file(source, destination)
        else:
            shutil.copy2(source, destination)

        if show_output:
            print_colored(f"Copied {source} to {destination}.", "green")
        return True
    except Exception as e:
        if show_output:
            print_colored(f"Error copying file: {e}", "red")
        return False


def _copy_win32_file(source: Path, destination: Path) -> None:
    """Copy a file on Windows, preserving attributes and permissions.

    Raises:
        ImportError: If pywin32 is not installed.
    """
    try:
        import win32con  # type: ignore
        import win32file  # type: ignore
    except ImportError as e:
        msg = "pywin32 is required for copying files on Windows."
        raise ImportError(msg) from e

    # Copy the file with metadata
    shutil.copy2(source, destination)

    # Ensure the destination file is not read-only
    destination.chmod(source.stat().st_mode)

    # Set file attributes to match the source
    source_attributes = win32file.GetFileAttributes(str(source))
    win32file.SetFileAttributes(str(destination), source_attributes)

    # Ensure the file is closed and not locked
    win32file.CreateFile(
        str(destination),
        win32con.GENERIC_READ | win32con.GENERIC_WRITE,
        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
        None,
        win32con.OPEN_EXISTING,
        win32con.FILE_ATTRIBUTE_NORMAL,
        None,
    ).Close()


def move_file(
    source: str | Path,
    destination: str | Path,
    overwrite: bool = False,
    show_output: bool = True,
) -> bool:
    """Move a file from source to destination.

    Args:
        source: The source file path.
        destination: The destination file path.
        overwrite: Whether to overwrite the destination file if it already exists.
        show_output: Whether to print output.
    """
    try:
        source = Path(source)
        destination = Path(destination)

        if not overwrite and destination.exists():
            if show_output:
                print_colored(
                    f"Error: Destination file {destination} already exists. Use overwrite=True to overwrite it.",
                    "yellow",
                )
            return False

        shutil.move(str(source), str(destination))
        if show_output:
            print_colored(f"Moved {source} to {destination}.", "green")
        return True
    except Exception as e:
        print_colored(f"Error moving file: {e}", "red")
        return False
