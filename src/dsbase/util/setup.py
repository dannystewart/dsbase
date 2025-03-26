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
        source = "from PyPI" if self.is_pypi_version else "local dev"
        return f"{self.package_name} v{self.version} ({source})"


def dsbase_setup() -> VersionInfo:
    """Configure the system with standard setup options.

    Sets up exception handling and automatically records version information.

    Returns:
        VersionInfo object with version details. The return isn't needed if you aren't going to use
        it for anything, but it's available in case you need version information for something.
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


def find_package_by_entry_point(script_name: str) -> str | None:
    """Find package name by checking if the script is an entry point.

    Returns:
        The package name if found, or None if not.
    """
    try:
        for dist in importlib.metadata.distributions():
            try:
                entry_points = dist.entry_points
                for ep in entry_points:
                    if ep.name == script_name and ep.group in {"console_scripts", "gui_scripts"}:
                        return dist.metadata["Name"]
            except Exception:
                continue
    except Exception:
        pass
    return None


def find_package_by_config_files(module_path: Path) -> str | None:
    """Find package name by looking for configuration files up the directory tree.

    Returns:
        The package name if found, or None if not.
    """
    current_dir = module_path.parent
    while current_dir.name:
        for config_file in ["pyproject.toml", "setup.py", "setup.cfg"]:
            config_path = current_dir / config_file
            if config_path.exists():
                return current_dir.name
        current_dir = current_dir.parent
    return None


def get_caller_module_path() -> Path | None:
    """Get the path of the module that called this function's caller.

    Returns:
        The package name if found, or None if not.
    """
    frame = inspect.currentframe()
    if frame is None:
        return None

    try:  # Get the caller's caller frame
        caller_frame = frame.f_back
        if caller_frame is None or caller_frame.f_back is None:
            return None

        caller_module = inspect.getmodule(caller_frame.f_back)
        if (
            caller_module is None
            or not hasattr(caller_module, "__file__")
            or caller_module.__file__ is None
        ):
            return None

        return Path(caller_module.__file__)
    finally:
        del frame


def get_caller_package_name() -> str:
    """Determine the package name from the running script.

    Returns:
        The package name if detected, or the script name otherwise.
    """
    # Get the main script name
    main_script = Path(sys.argv[0])
    script_name = main_script.stem

    # Strategy 1: Check entry points
    package_name = find_package_by_entry_point(script_name)
    if package_name:
        return package_name

    # Strategy 2: Check module path for config files
    module_path = get_caller_module_path()
    if module_path:
        package_name = find_package_by_config_files(module_path)
        if package_name:
            return package_name

    # Fallback to script name
    return script_name


def is_editable_install(package_location: Path) -> bool:
    """Check if a package is installed in editable mode.

    Returns:
        True if it's an editable install, False otherwise.
    """
    return package_location.name.endswith(".egg-link")


def has_dev_markers_in_path(package_location: Path) -> bool:
    """Check if the package path contains development markers.

    Returns:
        True if development markers are found, False otherwise.
    """
    dev_markers = ["dev", "develop", "source", "src", "projects", "workspace", "monorepo"]
    path_str = str(package_location).lower()
    return any(marker in path_str for marker in dev_markers)


def has_dev_files_in_ancestry(package_location: Path, max_levels: int = 8) -> bool:
    """Check if any parent directories contain development files.

    Args:
        package_location: The path to the package.
        max_levels: The maximum number of parent directories to check.

    Returns:
        True if development files are found, False otherwise.
    """
    parent_dir = package_location
    for _ in range(max_levels):
        if (parent_dir / ".git").exists() or (parent_dir / "pyproject.toml").exists():
            return True
        parent_dir = parent_dir.parent
    return False


def is_in_same_directory_tree(path1: Path, path2: Path) -> bool:
    """Check if two paths are in the same directory tree.

    Returns:
        True if the paths are in the same directory tree, False otherwise.
    """
    try:
        path1.relative_to(path2.parent.parent)
        return True
    except ValueError:
        try:
            path2.relative_to(path1.parent.parent)
            return True
        except ValueError:
            return False


def has_dev_version_markers(version: str) -> bool:
    """Check if a version string contains development markers.

    Returns:
        True if development markers are found, False otherwise.
    """
    return any(marker in version for marker in ["dev", "a", "b", "rc"])


def get_version_info(package_name: str) -> VersionInfo:
    """Get version information for a package.

    Args:
        package_name: The name of the package to check.

    Returns:
        VersionInfo object with version details.
    """
    try:
        version = importlib.metadata.version(package_name)
        is_pypi = True

        try:  # Get the package location
            dist = importlib.metadata.distribution(package_name)
            package_location = Path(str(dist.locate_file("")))

            if (  # Run through checks to determine if this is a development version
                is_editable_install(package_location)
                or has_dev_markers_in_path(package_location)
                or has_dev_files_in_ancestry(package_location)
                or has_dev_version_markers(version)
                or is_in_same_directory_tree(
                    Path(sys.argv[0]).resolve(), package_location.resolve()
                )
            ):
                is_pypi = False

        except Exception:  # If an error occurs during detection, assume it's a dev version
            is_pypi = False

        return VersionInfo(package_name, version, is_pypi)

    # If package metadata isn't found, assume it's a dev version not properly installed
    except importlib.metadata.PackageNotFoundError:
        return VersionInfo(package_name, "unknown", False)
