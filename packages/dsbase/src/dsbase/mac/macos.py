"""macOS-specific functions and utilities."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def get_timestamps(file: str | Path) -> tuple[str, str]:
    """Get file creation and modification timestamps. macOS only, as it relies on GetFileInfo.

    Returns:
        ctime: The creation timestamp.
        mtime: The modification timestamp.
    """
    ctime = subprocess.check_output(["GetFileInfo", "-d", str(file)]).decode().strip()
    mtime = subprocess.check_output(["GetFileInfo", "-m", str(file)]).decode().strip()
    return ctime, mtime


def set_timestamps(file: str | Path, ctime: str | None = None, mtime: str | None = None) -> None:
    """Set file creation and/or modification timestamps. macOS only, as it relies on SetFile.

    Args:
        file: The file to set the timestamps on.
        ctime: The creation timestamp to set. If None, creation time won't be set.
        mtime: The modification timestamp to set. If None, modification time won't be set.

    Raises:
        ValueError: If both ctime and mtime are None.
    """
    if ctime is None and mtime is None:
        msg = "At least one of ctime or mtime must be set."
        raise ValueError(msg)
    if ctime:
        subprocess.run(["SetFile", "-d", ctime, str(file)], check=False)
    if mtime:
        subprocess.run(["SetFile", "-m", mtime, str(file)], check=False)


def show_notification(
    message: str, title: str, subtitle: str | None = None, sound: bool = False
) -> None:
    """Display a macOS system notification using osascript.

    Args:
        message: The main notification message.
        title: The notification title.
        subtitle: An optional subtitle for the notification.
        sound: Whether to play the default notification sound. Defaults to False.

    Raises:
        subprocess.CalledProcessError: If the osascript command fails.
    """
    script_parts = ["display notification", f'"{message}"', f'with title "{title}"']

    if subtitle:
        script_parts.append(f'subtitle "{subtitle}"')

    if sound:
        script_parts.append('sound name "default"')

    script = " ".join(script_parts)

    try:
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        raise
