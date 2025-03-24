# pylint: disable=too-many-branches
from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from dsbase.text import print_colored

if TYPE_CHECKING:
    from pathlib import Path


def sha256_checksum(filename: Path, block_size: int = 65536) -> str:
    """Generate SHA-256 hash of a file.

    Args:
        filename: The file path.
        block_size: The block size to use when reading the file. Defaults to 65536.

    Returns:
        str: The SHA-256 hash of the file.
    """
    sha256 = hashlib.sha256()
    with filename.open("rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            sha256.update(block)
    return sha256.hexdigest()


def compare_files_by_mtime(file1: Path, file2: Path) -> float:
    """Compare two files based on modification time.

    Args:
        file1: The first file path.
        file2: The second file path.

    Returns:
        The difference in modification time between the two files.
    """
    stat1 = file1.stat()
    stat2 = file2.stat()
    return stat1.st_mtime - stat2.st_mtime


def find_duplicate_files_by_hash(files: list[Path]) -> None:
    """Find and print duplicate files by comparing their SHA-256 hashes.

    Args:
        files: A list of file paths.
    """
    hash_map = {}
    duplicates_found = False

    for file_path in files:
        if file_path.is_file():
            file_hash = sha256_checksum(file_path)
            if file_hash not in hash_map:
                hash_map[file_hash] = [file_path]
            else:
                hash_map[file_hash].append(file_path)
                duplicates_found = True

    for file_hash, file_list in hash_map.items():
        if len(file_list) > 1:
            print("\nHash:", file_hash)
            print_colored("Duplicate files:", "yellow")
            for duplicate_file in file_list:
                print(f"  - {duplicate_file}")

    if not duplicates_found:
        print_colored("\nNo duplicates found!", "green")
