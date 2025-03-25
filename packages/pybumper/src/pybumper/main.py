"""Version management tool for Python projects."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dsbase.util import dsbase_setup

from pybumper.bump_type import BumpType
from pybumper.version_bumper import VersionBumper

dsbase_setup()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "type",
        nargs="*",
        default=[BumpType.PATCH],
        help="version bump type(s): major, minor, patch, dev, alpha, beta, rc, post, or x.y.z",
    )
    parser.add_argument(
        "-p",
        "--package",
        help="package name to bump (e.g., dsbase, dsbin). Auto-detected if not provided.",
    )
    parser.add_argument("-f", "--force", action="store_true", help="skip confirmation prompt")
    parser.add_argument(
        "-m", "--message", help="custom commit message (default: 'Bump version to x.y.z')"
    )

    # Mutually exclusive group for push options
    push_group = parser.add_mutually_exclusive_group()
    push_group.add_argument(
        "--keep-version",
        action="store_true",
        help="tag and push the current version without incrementing",
    )
    push_group.add_argument(
        "--no-push",
        action="store_true",
        help="commit and tag changes but don't push to remote",
    )

    return parser.parse_args()


def detect_package(package_arg: str | None = None) -> tuple[str, Path]:
    """Detect package and relevant paths.

    Args:
        package_arg: An optional package name provided by the user.

    Returns:
        A tuple of (package_name, package_path).
    """
    # Auto-detect package if not provided
    if package_arg is None:
        package_name, package_path = auto_detect_package()
    else:
        package_name, package_path = find_from_monorepo_root(package_arg)

    # Verify package exists
    if not package_path.exists():
        print(f"Error: Package directory '{package_path}' not found")
        sys.exit(1)

    return package_name, package_path


def auto_detect_package() -> tuple[str, Path]:
    """Try to determine the package from the current directory."""
    # Try to determine the package from current directory
    current_dir = Path.cwd()

    # Check if we're in a package directory
    if current_dir.name == "dsbase" and current_dir.parent.name == "src":
        package_name = "dsbase"  # We're already in the package directory
        package_path = current_dir
        return package_name, package_path
    if current_dir.parent.name == "packages":
        package_name = current_dir.name  # We're already in the package directory
        package_path = current_dir
        return package_name, package_path
    # Check if we're in the monorepo root
    if (current_dir / "src" / "dsbase").exists() or (current_dir / "packages").exists():
        print("Error: You're in the monorepo root. Please specify a package with --package.")
    else:
        print("Error: Could not auto-detect package. Please specify a package with --package.")
    sys.exit(1)


def find_from_monorepo_root(package_name: str) -> tuple[str, Path]:
    """Find a package by name from the monorepo root."""
    # First, check if we're already in the monorepo
    current_dir = Path.cwd()

    # Try to find monorepo root
    if (current_dir / "src" / "dsbase").exists() or (current_dir / "packages").exists():
        monorepo_root = current_dir  # We're in the monorepo root
    else:
        # Try to find monorepo root by going up directories
        monorepo_root = None
        test_dir = current_dir

        for _ in range(3):  # Go up to 3 levels to find monorepo root
            if (test_dir / "src" / "dsbase").exists() or (test_dir / "packages").exists():
                monorepo_root = test_dir
                break
            parent = test_dir.parent
            if parent == test_dir:  # Reached filesystem root
                break
            test_dir = parent

        if monorepo_root is None:
            print("Error: Could not find monorepo root. Please run from within the monorepo.")
            sys.exit(1)

    # Now determine package path
    if package_name == "dsbase":
        package_path = monorepo_root / "src" / "dsbase"
    else:
        package_path = monorepo_root / "packages" / package_name

    return package_name, package_path


def main() -> None:
    """Perform version bump."""
    args = parse_args()

    # Detect package and paths
    package_name, package_path = detect_package(args.package)

    # Save the original directory and change to the package directory
    original_dir = Path.cwd()
    os.chdir(package_path)

    try:  # Pass package name to VersionBumper
        VersionBumper(args, package_name).perform_bump()
    finally:  # Change back to original directory
        os.chdir(original_dir)


if __name__ == "__main__":
    main()
