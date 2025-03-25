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


def detect_package(package_arg: str | None = None) -> tuple[str, Path, Path]:
    """Detect package and relevant paths.

    Args:
        package_arg: An optional package name provided by the user.

    Returns:
        A tuple of (package_name, package_path, original_dir).
    """
    original_dir = Path.cwd()
    monorepo_root = None
    package_name = package_arg

    # Auto-detect package if not provided
    if package_name is None:
        from dsbase import LocalLogger

        # Try to determine the package from current directory
        current_dir = Path.cwd()
        logger = LocalLogger().get_logger()

        # Check if we're in a package directory
        if current_dir.name == "dsbase" and current_dir.parent.name == "src":
            package_name = "dsbase"
            monorepo_root = current_dir.parent.parent
        elif current_dir.parent.name == "packages":
            package_name = current_dir.name
            monorepo_root = current_dir.parent.parent
        else:
            # Check if we're in the monorepo root
            if (current_dir / "src" / "dsbase").exists() or (current_dir / "packages").exists():
                logger.error("You're in the monorepo root. Please specify a package name.")
            else:
                logger.error("Could not auto-detect package. Please specify a package name.")
            sys.exit(1)

        logger.debug("Auto-detected package: %s", package_name)

    # If we didn't determine monorepo_root yet, assume current directory is monorepo root
    if monorepo_root is None:
        monorepo_root = original_dir

    # Determine package path
    if package_name == "dsbase":
        package_path = monorepo_root / "src" / "dsbase"
    else:
        package_path = monorepo_root / "packages" / package_name

    # Verify package exists
    if not package_path.exists():
        print(f"Error: Package directory '{package_path}' not found")
        sys.exit(1)

    return package_name, package_path, original_dir


def main() -> None:
    """Perform version bump."""
    args = parse_args()

    # Detect package and paths
    package_name, package_path, original_dir = detect_package(args.package)

    # Change to package directory
    os.chdir(package_path)

    try:  # Pass package name to VersionBumper
        VersionBumper(args, package_name).perform_bump()
    finally:  # Change back to original directory
        os.chdir(original_dir)


if __name__ == "__main__":
    main()
