from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from packaging import version


@dataclass
class VersionInfo:
    """Package version information."""

    package: str
    current: str | None = None
    latest: str | None = None
    source: str | None = None
    is_development: bool = False

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

    def __str__(self) -> str:
        """String representation of version info."""
        version_str = f"{self.package} v{self.current or 'unknown'}"
        if self.is_development:
            version_str += " (development)"
        else:
            version_str += f" ({self.source or 'unknown'})"

        if self.update_available:
            version_str += f" - update available: v{self.latest}"

        return version_str


class PackageSource(StrEnum):
    """Source for package version information."""

    PYPI = "pypi"
    GITHUB = "github"
    GITLAB = "gitlab"
    GIT = "git"
    AUTO = "auto"
