"""Version checking utilities for Python packages from various sources."""

from __future__ import annotations

import importlib
import importlib.metadata
import inspect
import subprocess
import sys
from pathlib import Path
from typing import Any

import requests
from packaging import version

from polykit.packages.types import PackageSource, VersionInfo


class VersionChecker:
    """Check for package versions from various sources."""

    def get_installed_version(self, package: str) -> str | None:
        """Get the currently installed version of a package.

        Args:
            package: The name of the package to check.

        Returns:
            The version string, or None if not installed.
        """
        try:
            import importlib.metadata

            return importlib.metadata.version(package)
        except (importlib.metadata.PackageNotFoundError, ImportError):
            return None

    def get_pypi_version(self, package: str) -> str | None:
        """Get the latest version of a package from PyPI.

        Args:
            package: The name of the package to check.

        Returns:
            The latest version string or None if not found.
        """
        try:
            response = requests.get(f"https://pypi.org/pypi/{package}/json", timeout=5)
            if response.status_code == 200:
                return response.json()["info"]["version"]
            return None
        except Exception:
            return None

    def get_git_version(self, repo_url: str, tag_prefix: str = "v") -> str | None:
        """Get the latest version from a Git repository's tags.

        Args:
            repo_url: The URL of the Git repository.
            tag_prefix: The prefix used for version tags (default: 'v').

        Returns:
            The latest version string or None if not found.
        """
        try:
            result = subprocess.run(
                ["git", "ls-remote", "--tags", repo_url],
                capture_output=True,
                text=True,
                check=True,
            )
            # Get all version tags and clean them up
            versions = []
            for ref in result.stdout.splitlines():
                tag = ref.split("/")[-1]
                # Extract version part after the prefix
                if tag.startswith(tag_prefix):
                    # Clean up Git ref notation and parse version
                    clean_tag = tag.split("^")[0].removeprefix(tag_prefix)
                    try:
                        versions.append(version.parse(clean_tag))
                    except version.InvalidVersion:
                        continue

            # Sort with packaging.version comparison
            if versions:
                return str(max(versions))
            return None

        except subprocess.CalledProcessError:
            return None

    def get_github_version(
        self,
        owner: str,
        repo: str,
        use_ssh: bool = False,
        tag_prefix: str = "v",
    ) -> str | None:
        """Get the latest version from a GitHub repository.

        Args:
            owner: The GitHub username or organization.
            repo: The repository name.
            use_ssh: Whether to use SSH URL format (default: False).
            tag_prefix: The prefix used for version tags (default: 'v').

        Returns:
            The latest version string or None if not found.
        """
        if use_ssh:
            url = f"git@github.com:{owner}/{repo}.git"
        else:
            url = f"https://github.com/{owner}/{repo}.git"

        return self.get_git_version(url, tag_prefix)

    def get_gitlab_version(
        self,
        host: str,
        owner: str,
        repo: str,
        use_ssh: bool = False,
        tag_prefix: str = "v",
    ) -> str | None:
        """Get the latest version from a GitLab repository.

        Args:
            host: The GitLab host (e.g., 'gitlab.com').
            owner: The GitLab username or group.
            repo: The repository name.
            use_ssh: Whether to use SSH URL format (default: False).
            tag_prefix: The prefix used for version tags (default: 'v').

        Returns:
            The latest version string or None if not found.
        """
        url = f"git@{host}:{owner}/{repo}.git" if use_ssh else f"https://{host}/{owner}/{repo}.git"

        return self.get_git_version(url, tag_prefix)

    def check_package(
        self,
        package: str,
        source: PackageSource = PackageSource.AUTO,
        **kwargs: Any,
    ) -> VersionInfo:
        """Check a package's installed and latest versions.

        Args:
            package: The name of the package to check.
            source: Where to check for the latest version.
            **kwargs: Additional arguments for the specific source checker.
                For GitHub: owner, repo, use_ssh, tag_prefix
                For GitLab: host, owner, repo, use_ssh, tag_prefix
                For Git: repo_url, tag_prefix

        Returns:
            VersionInfo containing current and latest versions.

        Raises:
            ValueError: If required arguments are missing for the source.
        """
        current = self.get_installed_version(package)
        is_development = self.is_development_version(package)
        latest = None

        if source == PackageSource.AUTO:
            # Try PyPI first, then fallback
            if latest := self.get_pypi_version(package):
                source = PackageSource.PYPI

        elif source == PackageSource.PYPI:
            latest = self.get_pypi_version(package)

        elif source == PackageSource.GITHUB:
            owner = kwargs.get("owner")
            repo = kwargs.get("repo", package)
            use_ssh = kwargs.get("use_ssh", False)
            tag_prefix = kwargs.get("tag_prefix", "v")

            if not owner:
                msg = "GitHub owner is required"
                raise ValueError(msg)

            latest = self.get_github_version(owner, repo, use_ssh, tag_prefix)

        elif source == PackageSource.GITLAB:
            host = kwargs.get("host", "gitlab.com")
            owner = kwargs.get("owner")
            repo = kwargs.get("repo", package)
            use_ssh = kwargs.get("use_ssh", False)
            tag_prefix = kwargs.get("tag_prefix", "v")

            if not owner:
                msg = "GitLab owner is required"
                raise ValueError(msg)

            latest = self.get_gitlab_version(host, owner, repo, use_ssh, tag_prefix)

        elif source == PackageSource.GIT:
            repo_url = kwargs.get("repo_url")
            tag_prefix = kwargs.get("tag_prefix", "v")

            if not repo_url:
                msg = "Git repository URL is required"
                raise ValueError(msg)

            latest = self.get_git_version(repo_url, tag_prefix)

        return VersionInfo(package, current, latest, source, is_development)

    def is_development_version(self, package: str) -> bool:
        """Determine if the installed package is a development version.

        Args:
            package: The name of the package to check.

        Returns:
            True if it's a development version, False if it's from PyPI or not installed.
        """
        try:
            import importlib.metadata
            import sys
            from pathlib import Path

            # Get the package location
            dist = importlib.metadata.distribution(package)
            package_location = Path(str(dist.locate_file("")))

            # Check for editable install
            if package_location.name.endswith(".egg-link"):
                return True

            # Check for development markers in path
            dev_markers = ["dev", "develop", "source", "src", "projects", "workspace", "monorepo"]
            if any(marker in str(package_location).lower() for marker in dev_markers):
                return True

            # Check for development files in ancestry
            parent_dir = package_location
            for _ in range(8):  # Check up to 8 levels up
                if (parent_dir / ".git").exists() or (parent_dir / "pyproject.toml").exists():
                    return True
                parent_dir = parent_dir.parent

            # Check for development version indicators in the version string
            version_str = dist.version
            if any(marker in version_str for marker in ["dev", "a", "b", "rc"]):
                return True

            # Check if in same directory tree as current script
            script_path = Path(sys.argv[0]).resolve()
            package_path = package_location.resolve()
            try:
                script_path.relative_to(package_path.parent.parent)
                return True
            except ValueError:
                try:
                    package_path.relative_to(script_path.parent.parent)
                    return True
                except ValueError:
                    pass

            # If we've passed all checks, it's likely a PyPI version
            return False

        except (importlib.metadata.PackageNotFoundError, Exception):
            # If any error occurs, assume it's not a development version
            return False

    @staticmethod
    def get_caller_package_name() -> str:
        """Determine the package name from the running script.

        Returns:
            The package name if detected, or the script name otherwise.
        """
        # Get the main script name
        main_script = Path(sys.argv[0])
        script_name = main_script.stem

        # Strategy 1: Check entry points
        package_name = VersionChecker.find_package_by_entry_point(script_name)
        if package_name:
            return package_name

        # Strategy 2: Check module path for config files
        module_path = VersionChecker.get_caller_module_path()
        if module_path:
            package_name = VersionChecker.find_package_by_config_files(module_path)
            if package_name:
                return package_name

        # Fallback to script name
        return script_name

    @staticmethod
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
                        if ep.name == script_name and ep.group in {
                            "console_scripts",
                            "gui_scripts",
                        }:
                            return dist.metadata["Name"]
                except Exception:
                    continue
        except Exception:
            pass
        return None

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def is_editable_install(package_location: Path) -> bool:
        """Check if a package is installed in editable mode.

        Returns:
            True if it's an editable install, False otherwise.
        """
        return package_location.name.endswith(".egg-link")

    @staticmethod
    def has_dev_markers_in_path(package_location: Path) -> bool:
        """Check if the package path contains development markers.

        Returns:
            True if development markers are found, False otherwise.
        """
        dev_markers = ["dev", "develop", "source", "src", "projects", "workspace", "monorepo"]
        path_str = str(package_location).lower()
        return any(marker in path_str for marker in dev_markers)

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def has_dev_version_markers(version: str) -> bool:
        """Check if a version string contains development markers.

        Returns:
            True if development markers are found, False otherwise.
        """
        return any(marker in version for marker in ["dev", "a", "b", "rc"])

    @staticmethod
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
                    VersionChecker.is_editable_install(package_location)
                    or VersionChecker.has_dev_markers_in_path(package_location)
                    or VersionChecker.has_dev_files_in_ancestry(package_location)
                    or VersionChecker.has_dev_version_markers(version)
                    or VersionChecker.is_in_same_directory_tree(
                        Path(sys.argv[0]).resolve(), package_location.resolve()
                    )
                ):
                    is_pypi = False

            except Exception:  # If an error occurs during detection, assume it's a dev version
                is_pypi = False

            return VersionInfo(package_name, version, is_development=not is_pypi)

        # If package metadata isn't found, assume it's a dev version not properly installed
        except importlib.metadata.PackageNotFoundError:
            return VersionInfo(package_name, "unknown", is_development=False)
