from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

from natsort import natsorted
from send2trash import send2trash

from polykit.cli import confirm_action

if TYPE_CHECKING:
    from collections.abc import Callable
    from logging import Logger

# Type alias due to FileManager having a `list` method
PathList = list[Path]


class PolyFiles:
    """A utility class with a comprehensive set of methods for common file operations.

    It supports listing files with filtering and sorting options, safe file deletion with trash bin
    support, and file copying and moving with overwrite protection. It also includes a method for
    detecting duplicate files using SHA-256 hashing.
    """

    @classmethod
    def list(
        cls,
        path: Path,  # noqa: A002
        extensions: str | list[str] | None = None,
        recurse: bool = False,
        exclude: str | list[str] | None = None,
        hidden: bool = False,
        sort_key: Callable[..., Any] | None = None,
        reverse: bool = False,
        logger: Logger | None = None,
    ) -> list[Path]:
        """List all files in a directory that match the given criteria.

        Args:
            path: The directory to search.
            extensions: The file extensions to include. If None, all files will be included.
            recurse: Whether to search recursively.
            exclude: Glob patterns to exclude.
            hidden: Whether to include hidden files.
            sort_key: A function to use for sorting the files.
            reverse: Whether to reverse the sort order.
            logger: Optional logger for operation information.

        Returns:
            A list of file paths as Path objects.
        """
        if extensions:
            # Handle both single string and list inputs
            ext_list = [extensions] if isinstance(extensions, str) else extensions
            # Handle extensions with or without dots
            ext_list = [ext.lstrip(".") for ext in ext_list]
            glob_patterns = [f"*.{ext}" for ext in ext_list]
        else:
            glob_patterns = ["*"]

        files_filtered: list[Path] = []
        for pattern in glob_patterns:
            files = path.rglob(pattern) if recurse else path.glob(pattern)
            try:
                files_filtered.extend(
                    file
                    for file in files
                    if file.is_file()
                    and (hidden or not file.name.startswith("."))
                    and not (exclude and any(file.match(pattern) for pattern in exclude))
                )
            except FileNotFoundError:
                if logger:
                    logger.error("Error accessing file while searching %s: File not found", pattern)

        sort_function = sort_key or (lambda x: x.stat().st_mtime)
        return natsorted(files_filtered, key=sort_function, reverse=reverse)

    @classmethod
    def delete(
        cls, paths: Path | PathList, dry_run: bool = False, logger: Logger | None = None
    ) -> tuple[int, int, list[str] | None]:
        """Safely move files to the trash or delete them permanently if necessary.

        Args:
            paths: The file path(s) to delete.
            dry_run: If True, report what would happen without making changes.
            logger: Optional logger for operation information.

        Returns:
            A tuple containing: (successful_deletions, failed_deletions, dry_run_messages).
            The dry_run_messages list is only populated when dry_run=True.
        """
        # Initialize tracking variables
        file_list = [paths] if isinstance(paths, Path) else paths
        successful = 0
        failed = 0
        dry_run_messages = [] if dry_run else None

        # Log dry run mode
        if dry_run and logger:
            logger.warning("NOTE: Dry run, not actually deleting!")

        # Process each file
        for file_path in file_list:
            # Skip non-existent files
            if not file_path.exists():
                failed += 1
                if logger:
                    logger.warning("File %s does not exist.", file_path.name)
                continue

            # Handle file based on dry run mode
            if dry_run:
                if cls._handle_dry_run_delete(file_path, logger, dry_run_messages):
                    successful += 1
                else:
                    failed += 1
            # First try sending to trash
            elif cls._try_trash_file(file_path, logger) or cls._try_permanent_delete(
                file_path, logger
            ):
                successful += 1
            else:
                failed += 1

        # Log summary if not in dry run mode
        if logger and not dry_run:
            message = f"{successful} file{'s' if successful != 1 else ''} trashed."
            if failed > 0:
                message += f" Failed to delete {failed} file{'s' if failed != 1 else ''}."
            logger.info(message)

        return successful, failed, dry_run_messages

    @classmethod
    def _handle_dry_run_delete(
        cls, file_path: Path, logger: Logger | None, dry_run_messages: list[str] | None
    ) -> bool:
        """Handle file deletion simulation in dry run mode.

        Args:
            file_path: The file to simulate deletion for.
            logger: Optional logger for messages.
            dry_run_messages: A list to collect dry run messages, or None.

        Returns:
            True, as the simulation is always successful.
        """
        message = f"Would delete: {file_path}"
        if logger:
            logger.info(message)
        if dry_run_messages is not None:
            dry_run_messages.append(message)
        return True

    @classmethod
    def _try_trash_file(cls, file_path: Path, logger: Logger | None) -> bool:
        """Attempt to move a file to the trash.

        Returns:
            True if the file was successfully trashed, False otherwise.
        """
        try:
            send2trash(str(file_path))
            if logger:
                logger.info("✔ Trashed %s", file_path.name)
            return True
        except Exception as e:  # Trash failed, log the error
            if logger:
                logger.error("Failed to send file to trash: %s", str(e))
            return False

    @classmethod
    def _try_permanent_delete(cls, file_path: Path, logger: Logger | None) -> bool:
        """Attempt to permanently delete a file after user confirmation.

        Returns:
            True if the file was successfully deleted, False otherwise.
        """
        if confirm_action("Do you want to permanently delete the file?"):
            try:
                file_path.unlink()
                if logger:
                    logger.info("✔ Permanently deleted %s", file_path.name)
                return True
            except OSError as err:
                if logger:
                    logger.error("Error: Failed to permanently delete %s: %s", file_path.name, err)

        return False

    @classmethod
    def copy(
        cls, source: Path, destination: Path, overwrite: bool = True, logger: Logger | None = None
    ) -> bool:
        """Copy a file from source to destination.

        Args:
            source: The source file path.
            destination: The destination file path.
            overwrite: Whether to overwrite the destination file if it already exists.
            logger: Optional logger for operation information.
        """
        try:
            if not overwrite and destination.exists():
                if logger:
                    logger.warning(
                        "Error: Destination file %s already exists. Use overwrite=True to overwrite it.",
                        destination,
                    )
                return False

            shutil.copy2(source, destination)

            if logger:
                logger.info("Copied %s to %s.", source, destination)
            return True
        except Exception as e:
            if logger:
                logger.error("Error copying file: %s", str(e))
            return False

    @classmethod
    def move(
        cls, source: Path, destination: Path, overwrite: bool = False, logger: Logger | None = None
    ) -> bool:
        """Move a file from source to destination.

        Args:
            source: The source file path.
            destination: The destination file path.
            overwrite: Whether to overwrite the destination file if it already exists.
            logger: Optional logger for operation information.
        """
        try:
            if not overwrite and destination.exists():
                if logger:
                    logger.warning(
                        "Error: Destination file %s already exists. Use overwrite=True to overwrite it.",
                        destination,
                    )
                return False

            shutil.move(str(source), str(destination))
            if logger:
                logger.info("Moved %s to %s.", source, destination)
            return True
        except Exception as e:
            if logger:
                logger.error("Error moving file: %s", str(e))
            return False

    @classmethod
    def find_dupes_by_hash(
        cls, files: PathList, logger: Logger | None = None
    ) -> dict[str, list[Path]]:
        """Find duplicate files by comparing their SHA-256 hashes.

        Args:
            files: A list of file paths.
            logger: Optional logger for operation information.

        Returns:
            A dictionary mapping file hashes to lists of duplicate files.
        """
        hash_map: dict[str, list[Path]] = {}
        duplicates_found = False

        for file_path in files:
            if file_path.is_file():
                file_hash = cls.sha256_checksum(file_path)
                if file_hash not in hash_map:
                    hash_map[file_hash] = [file_path]
                else:
                    hash_map[file_hash].append(file_path)
                    duplicates_found = True

        if logger:
            if not duplicates_found:
                logger.info("No duplicates found!")
            else:
                for file_hash, file_list in hash_map.items():
                    if len(file_list) > 1:
                        logger.info("\nHash: %s", file_hash)
                        logger.warning("Duplicate files:")
                        for duplicate_file in file_list:
                            logger.info("  - %s", duplicate_file)

        # Return only entries with duplicates
        return {k: v for k, v in hash_map.items() if len(v) > 1}

    @staticmethod
    def get_timestamps(file: Path) -> tuple[str, str]:
        """Get file creation and modification timestamps. macOS only, as it relies on GetFileInfo.

        Returns:
            ctime: The creation timestamp.
            mtime: The modification timestamp.
        """
        ctime = subprocess.check_output(["GetFileInfo", "-d", str(file)]).decode().strip()
        mtime = subprocess.check_output(["GetFileInfo", "-m", str(file)]).decode().strip()
        return ctime, mtime

    @staticmethod
    def set_timestamps(file: Path, ctime: str | None = None, mtime: str | None = None) -> None:
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

    @staticmethod
    def compare_mtime(file1: Path, file2: Path) -> float:
        """Compare two files based on modification time.

        Args:
            file1: The first file path.
            file2: The second file path.

        Returns:
            The difference in modification time between the two files as a float.
        """
        stat1 = file1.stat()
        stat2 = file2.stat()
        return stat1.st_mtime - stat2.st_mtime

    @staticmethod
    def sha256_checksum(filename: Path, block_size: int = 65536) -> str:
        """Generate SHA-256 hash of a file.

        Args:
            filename: The file path.
            block_size: The block size to use when reading the file. Defaults to 65536.

        Returns:
            The SHA-256 hash of the file.
        """
        sha256 = hashlib.sha256()
        with filename.open("rb") as f:
            for block in iter(lambda: f.read(block_size), b""):
                sha256.update(block)
        return sha256.hexdigest()
