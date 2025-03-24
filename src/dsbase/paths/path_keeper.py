# ruff: noqa: D102

r"""PathKeeper: A friendly cross-platform path management utility.

PathKeeper simplifies working with application and user directories across different operating
systems, providing consistent access to standard locations while respecting platform conventions.

Platform-specific paths:
    Linux:
        data:      ~/.local/share/app_name
        config:    ~/.config/app_name
        cache:     ~/.cache/app_name
        logs:      ~/.cache/app_name/logs
        state:     ~/.local/state/app_name
        documents: ~/Documents

    macOS (adds `app_domain` if provided):
        data:      ~/Library/Application Support/app_domain/app_name
        config:    ~/Library/Preferences/app_name
        cache:     ~/Library/Caches/app_name
        logs:      ~/Library/Logs/app_name
        state:     ~/Library/Application Support/app_domain/app_name
        documents: ~/Documents

    Windows:
        data:      C:\\Users\\<user>\\AppData\\Local\\app_author\\app_name
        config:    C:\\Users\\<user>\\AppData\\Local\\app_author\\app_name\\Config
        cache:     C:\\Users\\<user>\\AppData\\Local\\app_author\\app_name\\Cache
        logs:      C:\\Users\\<user>\\AppData\\Local\\app_author\\app_name\\Logs
        state:     C:\\Users\\<user>\\AppData\\Local\\app_author\\app_name
        documents: C:\\Users\\<user>\\Documents

Examples:
    Basic usage:
        paths = PathKeeper("myapp")
        config_file = paths.from_config("settings.json")
        cache_dir = paths.from_cache("responses")

    With author and domain (recommended for macOS):
        paths = PathKeeper(
            app_name="MyApp",
            app_author="DeveloperName",
            app_domain_prefix="com.developername",
        )
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from platformdirs import PlatformDirs

from dsbase.env import EnvManager


@dataclass
class PathKeeper:
    """Manage paths in a friendly way.

    Args:
        app_name: Name of the application. Required due to the need for a base directory.
        app_author: Author of the application.
        app_domain_prefix: Domain prefix for macOS paths. Application name will be appended.
        version: Application version.

    Usage:
        paths = PathKeeper("dsmusic")

        db_path = paths.get_data_path("upload_log.db")
        cache_path = paths.get_cache_path("api_responses", "tracks.json")
        log_path = paths.get_log_path("debug.log")
    """

    app_name: str
    app_author: str | None = None
    app_domain_prefix: str | None = None
    version: str | None = None
    create_dirs: bool = True

    def __post_init__(self):
        # Get app author and domain prefix from environment variables if available
        env_man = EnvManager()
        env_man.add_var("PATHKEEPER_APP_AUTHOR", attr_name="app_author", required=False)
        env_man.add_var("PATHKEEPER_APP_DOMAIN_PREFIX", attr_name="app_domain", required=False)

        # Set these if they exist in the environment and weren't otherwise supplied
        if self.app_author is None and hasattr(env_man, "app_author") and env_man.app_author:
            self.app_author = env_man.app_author
        if self.app_domain_prefix is None and hasattr(env_man, "app_domain") and env_man.app_domain:
            self.app_domain_prefix = env_man.app_domain

        if sys.platform == "darwin" and self.app_domain_prefix:
            # For macOS, use domain-based path if provided
            normalized_name = self.app_name.lower().replace(" ", "")
            app_path = f"{self.app_domain_prefix}.{normalized_name}"
        else:
            app_path = self.app_name

        # Initialize platform directories and convert to Path objects
        self._dirs = PlatformDirs(
            appname=app_path,
            appauthor=self.app_author,
            version=self.version,
        )
        self._data_dir = Path(self._dirs.user_data_dir)
        self._cache_dir = Path(self._dirs.user_cache_dir)
        self._config_dir = Path(self._dirs.user_config_dir)
        self._log_dir = Path(self._dirs.user_log_dir)
        self._state_dir = Path(self._dirs.user_state_dir)

        if self.create_dirs:
            self._ensure_base_dirs()

    def _ensure_base_dirs(self) -> None:
        """Create base directories if they don't exist."""
        for dir_path in [
            self.data_dir,
            self.cache_dir,
            self.config_dir,
            self.log_dir,
            self.state_dir,
        ]:
            dir_path.parent.mkdir(parents=True, exist_ok=True)

    def _join_path(
        self, base_dir: Path, paths: tuple[str | Path, ...], no_create: bool = False
    ) -> Path:
        """Join paths and create parent directory if needed."""
        path = base_dir.joinpath(*paths)
        if self.create_dirs and not no_create:
            if not path.exists() or not path.is_file():
                path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def home_dir(self) -> Path:
        return Path.home()

    @property
    def documents_dir(self) -> Path:
        return Path(self.home_dir, "Documents")

    @property
    def downloads_dir(self) -> Path:
        return Path(self.home_dir, "Downloads")

    @property
    def music_dir(self) -> Path:
        return Path(self.home_dir, "Music")

    @property
    def pictures_dir(self) -> Path:
        return Path(self.home_dir, "Pictures")

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    @property
    def config_dir(self) -> Path:
        return self._config_dir

    @property
    def log_dir(self) -> Path:
        return self._log_dir

    @property
    def state_dir(self) -> Path:
        return self._state_dir

    @property
    def onedrive_dir(self) -> Path:
        """Get the platform-specific OneDrive base directory."""
        if sys.platform == "darwin":
            return Path(self.home_dir) / "Library/CloudStorage/OneDrive-Personal"
        if sys.platform == "win32":
            return Path(self.home_dir) / "OneDrive"
        msg = "OneDrive not supported on this platform"
        raise NotImplementedError(msg)

    def from_home(self, *paths: str | Path, no_create: bool = False) -> Path:
        """Get a path in the user's home directory.

        Args:
            *paths: Path components to join (e.g. 'subfolder', 'file.txt').
            no_create: Whether to avoid creating directories that don't exist.
        """
        return self._join_path(self.home_dir, paths, no_create)

    def from_documents(self, *paths: str | Path, no_create: bool = False) -> Path:
        """Get a path in the user's Documents directory.

        Args:
            *paths: Path components to join (e.g. 'subfolder', 'file.txt').
            no_create: Whether to avoid creating directories that don't exist.
        """
        return self._join_path(self.documents_dir, paths, no_create)

    def from_downloads(self, *paths: str | Path, no_create: bool = False) -> Path:
        """Get a path in the user's Downloads directory.

        Args:
            *paths: Path components to join (e.g. 'subfolder', 'file.txt').
            no_create: Whether to avoid creating directories that don't exist.
        """
        return self._join_path(self.downloads_dir, paths, no_create)

    def from_music(self, *paths: str | Path, no_create: bool = False) -> Path:
        """Get a path in the user's Music directory.

        Args:
            *paths: Path components to join (e.g. 'subfolder', 'file.txt').
            no_create: Whether to avoid creating directories that don't exist.
        """
        return self._join_path(self.music_dir, paths, no_create)

    def from_pictures(self, *paths: str | Path, no_create: bool = False) -> Path:
        """Get a path in the user's Pictures directory.

        Args:
            *paths: Path components to join (e.g. 'subfolder', 'file.txt').
            no_create: Whether to avoid creating directories that don't exist.
        """
        return self._join_path(self.pictures_dir, paths, no_create)

    def from_onedrive(self, *paths: str | Path, no_create: bool = False) -> Path:
        """Get a path in the user's OneDrive directory.

        Args:
            *paths: Path components to join (e.g. 'subfolder', 'file.txt').
            no_create: Whether to avoid creating directories that don't exist.
        """
        return self._join_path(self.onedrive_dir, paths, no_create)

    def from_data(self, *paths: str | Path, no_create: bool = False) -> Path:
        """Get a path in the data directory.

        Args:
            *paths: Path components to join (e.g. 'subfolder', 'file.txt').
            no_create: Whether to avoid creating directories that don't exist.
        """
        return self._join_path(self.data_dir, paths, no_create)

    def from_cache(self, *paths: str | Path, no_create: bool = False) -> Path:
        """Get a path in the cache directory.

        Args:
            *paths: Path components to join (e.g. 'subfolder', 'file.txt').
            no_create: Whether to avoid creating directories that don't exist.
        """
        return self._join_path(self.cache_dir, paths, no_create)

    def from_config(
        self, *paths: str | Path, no_create: bool = False, home_root: bool = False
    ) -> Path:
        """Get a path in the config directory.

        Args:
            *paths: Path components to join (e.g. 'subfolder', 'file.txt').
            no_create: Whether to avoid creating directories that don't exist.
            home_root: If True, use ~/.config instead of platform-specific location.
        """
        base = Path.home() / ".config" / self.app_name if home_root else self.config_dir
        return self._join_path(base, paths, no_create)

    def from_log(self, *paths: str | Path, no_create: bool = False) -> Path:
        """Get a path in the log directory.

        Args:
            *paths: Path components to join (e.g. 'subfolder', 'file.txt').
            no_create: Whether to avoid creating directories that don't exist.
        """
        return self._join_path(self.log_dir, paths, no_create)

    def from_state(self, *paths: str | Path, no_create: bool = False) -> Path:
        """Get a path in the state directory.

        Args:
            *paths: Path components to join (e.g. 'subfolder', 'file.txt').
            no_create: Whether to avoid creating directories that don't exist.
        """
        return self._join_path(self.state_dir, paths, no_create)

    def from_ssh(self, *paths: str | Path) -> Path:
        """Get a file or path from under the user's .ssh directory.

        Args:
            *paths: Path components to join (e.g. 'subfolder', 'file.txt').
        """
        return Path(self.home_dir, ".ssh").joinpath(*paths)

    def get_ssh_key(self, key_name: str = "id_ed25519") -> Path:
        """Get a specific SSH key file from the user's .ssh directory.

        Args:
            key_name: The name of the SSH key file (default is 'id_ed25519').
        """
        return self.from_ssh() / key_name
