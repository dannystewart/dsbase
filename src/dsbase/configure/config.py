from __future__ import annotations

import fnmatch
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

import tomlkit
import yaml
from tomlkit import TOMLDocument

from dsbase import LocalLogger, PathKeeper
from dsbase.configure.attr_dict import AttrDict
from dsbase.configure.watchers import ConfigWatcher
from dsbase.text import Text
from dsbase.util.deprecate import not_yet_implemented

if TYPE_CHECKING:
    from collections.abc import Callable
    from logging import Logger

T = TypeVar("T")

# Define the type for configuration settings
type SettingsDict = AttrDict[str, Any]


@not_yet_implemented("Configuration system is not yet implemented.")
class Config:
    """Configuration management with support for multiple file formats and automatic reloading."""

    # File loaders for supported configuration formats
    _FILE_LOADERS: ClassVar[dict[str, Callable[[Any], dict[str, Any]]]] = {
        ".yaml": yaml.safe_load,
        ".yml": yaml.safe_load,
        ".toml": tomlkit.load,
    }

    def __init__(self, config_name: str, auto_reload: bool = True, logger: Logger | None = None):
        """Initialize the configuration system.

        Args:
            config_name: Name of the configuration (used for paths).
            auto_reload: Whether to automatically reload on file changes.
            logger: Optional logger instance (defaults to LocalLogger).
        """
        self.config_name: str = config_name
        self.auto_reload: bool = auto_reload
        self.logger: Logger = logger or LocalLogger().get_logger()

        # Internal state
        self._lock: Lock = Lock()
        self._loaded: bool = False
        self._is_reloading: bool = False
        self._last_settings: SettingsDict | None = None
        self._old_settings: SettingsDict | None = None
        self._key_split_cache: dict[str, list[str]] = {}
        self._key_exists_cache: dict[str, bool] = {}
        self._excluded_change_warnings: set[str] = set()

        # Configuration settings
        self.settings: SettingsDict = AttrDict()

        # Load initial configuration
        self.reload()

        # Set up file watching if auto_reload is enabled
        if auto_reload:
            self.start_file_watching()

    @property
    def config_path(self) -> Path:
        """Get the path to the configuration directory."""
        return PathKeeper(self.config_name).config_dir

    def load_config_files(self) -> SettingsDict:
        """Load all configuration files from the config directory."""
        settings = AttrDict()
        config_dir = self.config_path

        # Get all config files and load them in order
        config_files = sorted(
            f for f in config_dir.rglob("*.*") if f.suffix.lower() in self._FILE_LOADERS
        )
        for file in config_files:
            self._load_file(file, settings)

        return settings

    def _load_file(self, file_path: Path, settings: SettingsDict) -> None:
        """Load a single configuration file."""
        try:
            loader = self._FILE_LOADERS[file_path.suffix.lower()]
            with file_path.open() as f:
                data = loader(f)
            if data:
                if isinstance(data, TOMLDocument):
                    data = self._convert_toml(data)
                settings.update(Config.merge_dict(AttrDict(data), settings))
        except Exception as e:
            self.logger.error("Failed to load %s: %s", file_path, str(e))

    def start_file_watching(self) -> None:
        """Set up file watching for the config directory and existing config files."""
        config_dir = self.config_path

        # Watch the config directory
        ConfigWatcher().watch_directory(str(config_dir), self.reload_on_file_change)

        # Watch individual config files
        config_files = sorted(
            f for f in config_dir.rglob("*.*") if f.suffix.lower() in self._FILE_LOADERS
        )
        for file in config_files:
            ConfigWatcher().watch_file(str(file), self.reload_on_file_change)

    def reload_on_file_change(self, changed_file_path: str) -> None:
        """Reload the configuration files when a file event occurs."""
        if not self.auto_reload:
            return

        self.reload()
        self.logger.debug("Config reloaded after file change: %s", Path(changed_file_path).name)

        # Refresh file watching to catch any new files
        self.start_file_watching()

    def reload(self, manual: bool = False) -> None:
        """Reload the configuration file."""
        # Skip if already loaded and not manual reload
        if self._loaded and not self.auto_reload and not manual:
            return

        # Skip if reloading is in progress
        if self._is_reloading:
            self.logger.warning("Skipping reload due to reload already in progress.")
            return

        # Set the flag to indicate a reload is in progress
        self._is_reloading = True
        try:
            with self._lock:
                self._initialize_config(manual)
                self._loaded = True  # Mark the configuration as loaded

        except Exception as e:
            self.logger.error("Failed to reload configuration: %s", str(e))
            raise

        finally:
            self._is_reloading = False  # Reset the reload flag

    def _initialize_config(self, manual: bool = False) -> None:
        """Initialize the configuration by loading and validating the config files."""
        new_settings = self.load_config_files()

        # Store the old settings then check for changes
        old_settings = self._last_settings
        changed_settings = (
            self.identify_changes(old_settings, new_settings)
            if old_settings is not None
            else set(Config.flatten_dict(new_settings).keys())
        )

        # Store the old settings temporarily
        self._old_settings = old_settings

        # Replace the instance settings with the new settings
        self._last_settings = new_settings
        self.settings = new_settings

        # Update configuration
        self._update_excluded_change_warnings()

        # Log changes
        if old_settings is not None:
            self._log_changes(changed_settings)

        # Clear temporary old settings
        self._old_settings = None

        # Clear caches when config changes
        self._key_split_cache.clear()
        self._key_exists_cache.clear()

        if manual and self.logger:
            self.logger.info("Manual reload successful!")

    def _log_changes(self, changed_settings: set[str]) -> None:
        """Log the changed settings."""
        if not changed_settings or not self.logger:
            return

        change_details = []
        for key in changed_settings:
            # Get changed values for logging
            old_value = (
                Config.flatten_dict(self._old_settings).get(key)
                if self._old_settings is not None
                else None
            )
            new_value = Config.flatten_dict(self.settings).get(key)

            # Truncate long values
            if isinstance(old_value, str):
                old_value = self._truncate_for_log(old_value)
            if isinstance(new_value, str):
                new_value = self._truncate_for_log(new_value)

            # Format change details
            change_details.append(f"{key}: {old_value!r} → {new_value!r}")

        if change_details:
            self.logger.debug("Changed %s", "\n".join(change_details))

    @staticmethod
    def _truncate_for_log(text: str) -> str:
        return Text.truncate(text, chars=50, strict=True, condensed=True)

    @staticmethod
    def identify_changes(
        old_config: dict[str, Any] | SettingsDict, new_config: dict[str, Any] | SettingsDict
    ) -> set[str]:
        """Detect changes between old and new configurations, including nested changes.

        Args:
            old_config: The old configuration (dict or AttrDict).
            new_config: The new configuration (dict or AttrDict).

        Returns:
            A set of strings representing the changed keys, with nested keys separated by dots.
        """
        old_flat = Config.flatten_dict(old_config)
        new_flat = Config.flatten_dict(new_config)
        all_keys = set(old_flat.keys()) | set(new_flat.keys())

        return {
            key
            for key in all_keys
            if key not in old_flat or key not in new_flat or old_flat[key] != new_flat[key]
        }

    def _split_key(self, key: str) -> list[str]:
        if key not in self._key_split_cache:
            self._key_split_cache[key] = key.split(".")
        return self._key_split_cache[key]

    def _should_warn_for_key(self, key: str) -> bool:
        """Check if a warning should be generated for the given key."""
        return not any(fnmatch.fnmatch(key, pattern) for pattern in self._excluded_change_warnings)

    def _log_missing_key_warning(self, full_path: str, default: Any) -> None:
        """Log a warning for a missing configuration key."""
        import traceback

        stack = traceback.extract_stack()
        caller = stack[-3]  # Get the caller's frame

        self.logger.warning(
            "Accessing non-existent configuration key: %s (using default: %r) - called from %s:%d in %s",
            full_path,
            default,
            caller.filename,
            caller.lineno,
            caller.name,
        )

    def _update_excluded_change_warnings(self) -> None:
        """Update the set of excluded warning patterns from configuration."""
        patterns = self.get("config.excluded_change_warnings", [])
        if isinstance(patterns, list):
            self._excluded_change_warnings = set(patterns)
        else:
            self.logger.warning(
                "Invalid excluded_change_warnings format detected in configuration: expected list, got %s",
                type(patterns),
            )
            self._excluded_change_warnings = set()

    @staticmethod
    def _convert_toml(toml_data: Any) -> dict[str, Any]:
        """Convert a TOMLDocument or nested TOML structures to a regular dictionary."""
        if hasattr(toml_data, "items"):
            result = {}
            for key, value in toml_data.items():
                if hasattr(value, "items"):
                    result[key] = Config._convert_toml(value)
                elif isinstance(value, list):
                    result[key] = [
                        Config._convert_toml(item) if hasattr(item, "items") else item
                        for item in value
                    ]
                else:
                    result[key] = value
            return result
        return toml_data

    @staticmethod
    def merge_dict(source: SettingsDict, destination: SettingsDict | None = None) -> SettingsDict:
        """Merge a source dictionary into a destination dictionary."""
        if destination is None:
            destination = AttrDict()
        elif isinstance(destination, dict):
            destination = AttrDict(destination)

        for key, value in source.items() if isinstance(source, dict) else source.to_dict().items():
            if not destination:
                return source
            if Config.is_dict_like(value):
                destination[key] = Config.merge_dict(value, destination.get(key, AttrDict()))
            else:
                destination[key] = value
        return destination

    @staticmethod
    def flatten_dict(d: dict[str, Any] | SettingsDict, parent_key: str = "") -> dict[str, Any]:
        """Flatten a nested dictionary."""
        items: list[tuple[str, Any]] = []
        for k, v in d.items() if isinstance(d, dict) else d.to_dict().items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if Config.is_dict_like(v):
                items.extend(Config.flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)

    @staticmethod
    def serialize_dict(obj: Any) -> Any:
        """Convert a dictionary to a serializable dictionary."""
        if isinstance(obj, AttrDict):
            return {k: Config.serialize_dict(v) for k, v in obj.items()}
        if isinstance(obj, dict):
            return {k: Config.serialize_dict(v) for k, v in obj.items()}
        return [Config.serialize_dict(v) for v in obj] if isinstance(obj, list) else obj

    @staticmethod
    def is_dict_like(obj: Any) -> bool:
        """Check if an object is dict-like (dict or AttrDict)."""
        return isinstance(obj, dict | AttrDict)

    def get(self, key: str, default: T = None) -> Any | T:
        """Get a configuration value by key name, with an optional default value."""
        keys = self._split_key(key)
        value = self.settings
        current_path = []

        # Check existence cache first
        if key in self._key_exists_cache and not self._key_exists_cache[key]:
            if self._should_warn_for_key(key):
                self._log_missing_key_warning(key, default)
            return default
        for k in keys:
            current_path.append(k)
            if isinstance(value, AttrDict | dict) and k in value:
                value = value[k]
            else:
                full_path = ".".join(current_path)
                self._key_exists_cache[key] = False  # Cache the miss
                if self._should_warn_for_key(full_path):
                    self._log_missing_key_warning(full_path, default)
                return default

        self._key_exists_cache[key] = True  # Cache the hit
        return AttrDict(value) if isinstance(value, dict) else value

    def __getattr__(self, item: str) -> Any:
        """Get a configuration value by attribute.

        Raises:
            AttributeError: If the key is not found in the configuration.
        """
        if item in self.settings:
            return self.settings[item]

        msg = f"Configuration key not found: {item}"
        raise AttributeError(msg)


class ConfigurationError(Exception):
    """Base class for configuration-related errors."""


class MissingConfigError(ConfigurationError):
    """Raised when a required configuration value is missing."""


class InvalidConfigError(ConfigurationError):
    """Raised when a configuration value is invalid."""


class SchemaValidationError(ConfigurationError):
    """Raised when schema validation fails."""
