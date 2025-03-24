"""Version checking utilities for Python packages from various sources."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import requests
from packaging import version


class PackageSource(StrEnum):
    """Source for package version information."""

    PYPI = "pypi"
    GITHUB = "github"
    GITLAB = "gitlab"
    GIT = "git"
    AUTO = "auto"


@dataclass
class VersionInfo:
    """Package version information."""

    package: str
    current: str | None = None
    latest: str | None = None
    source: str | None = None

    @property
    def is_latest(self) -> bool:
        """Check if current version is the latest."""
        if not self.current or not self.latest:
            return False
        return version.parse(self.current) >= version.parse(self.latest)

    @property
    def update_available(self) -> bool:
        """Check if an update is available."""
        if not self.current or not self.latest:
            return False
        return version.parse(self.latest) > version.parse(self.current)


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

        return VersionInfo(package, current, latest, source)
