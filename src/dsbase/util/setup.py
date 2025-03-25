from __future__ import annotations

import importlib.metadata
import inspect
import sys
from dataclasses import dataclass
from pathlib import Path

from dsbase.util.traceback import log_traceback


@dataclass
class VersionInfo:
    """Dataclass to store package version information."""

    package_name: str
    version: str
    is_pypi_version: bool

    def __str__(self) -> str:
        source = "PyPI" if self.is_pypi_version else "development"
        return f"{self.package_name} v{self.version} ({source})"


def dsbase_setup() -> VersionInfo:
    """Configure the system with standard setup options.

    Sets up exception handling and automatically records version information.

    Returns:
        VersionInfo object with version details.
    """
    # Configure exception handling
    sys.excepthook = lambda exctype, value, tb: log_traceback((exctype, value, tb))

    # Automatically determine package name
    package_name = get_caller_package_name()

    # Get and log version information
    version_info = get_version_info(package_name)

    from dsbase import EnvManager, LocalLogger

    env = EnvManager()
    env.add_bool("SHOW_VER")
    level = "DEBUG" if env.show_ver else "INFO"

    logger = LocalLogger().get_logger(level=level, simple=True)
    logger.debug("Starting %s", version_info)

    return version_info


def get_caller_package_name() -> str:
    """Automatically determine returns the package name of the calling module."""
    # Get the frame of the caller (two levels up from dsbase_setup)
    frame = inspect.currentframe()
    if frame is None:
        return "unknown"

    try:
        caller_frame = frame.f_back
        if caller_frame is None:
            return "unknown"

        # Get the module of the caller
        caller_module = inspect.getmodule(caller_frame)
        if caller_module is None:
            return "unknown"

        # If it's a top-level script with no package, use the filename
        if not caller_module.__package__:
            module_path = Path(caller_module.__file__ or "")
            return module_path.stem

        # Otherwise use the package name
        package_parts = caller_module.__package__.split(".")
        return package_parts[0]  # Top-level package name
    finally:  # Clean up references to avoid reference cycles
        del frame


def get_version_info(package_name: str) -> VersionInfo:
    """Get version information for a package. Returns VersionInfo object."""
    try:
        version = importlib.metadata.version(package_name)

        # Get the package location
        package_location = Path(str(importlib.metadata.distribution(package_name).locate_file("")))

        # Check if it's in site-packages (PyPI version) or not (development version)
        is_pypi = "site-packages" in str(package_location)

        return VersionInfo(package_name, version, is_pypi)

    except importlib.metadata.PackageNotFoundError:
        # If package metadata isn't found, it's a development version without proper installation
        return VersionInfo(package_name, "unknown", False)
