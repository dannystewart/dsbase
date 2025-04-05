from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from dotenv import load_dotenv

from polykit.core import Singleton
from polykit.env.types import PolyVar
from polykit.log import PolyLog

if TYPE_CHECKING:
    from collections.abc import Callable
    from logging import Logger

T = TypeVar("T")


@dataclass
class PolyEnv(metaclass=Singleton):
    """PolyEnv is an environment variable manager for Python applications.

    It handles loading from multiple `.env` files, type conversion, validation, and provides an
    elegant interface for accessing your environment configuration. It features:

    - Hierarchical loading from multiple `.env` files with smart precedence rules.
    - Type conversion to automatically convert environment strings to Python types.
    - Validation to ensure required variables are present and correctly formatted.
    - Attribute access for clean, IDE-friendly environment variable usage.
    - Secret masking to prevent sensitive values from appearing in logs.
    - Smart boolean parsing that understands various truthy/falsey string formats.
    - Singleton pattern ensuring consistent environment state throughout your application.

    Environment Loading Strategy:
    1. Loads from .env files in parent directories (up to user's home directory)
    2. Loads from the current directory's .env file
    3. Loads from ~/.env (user's home directory)
    4. Uses current environment variables
    5. Allows specifying custom files that override all of the above

    This hierarchical approach means more specific configurations (closer to the current directory)
    override broader ones. For example, if you have /home/user/.env and /home/user/project/.env,
    variables in the project-specific file will take precedence.

    For detailed logging for PolyEnv itself, set the ENV_DEBUG environment variable to '1'.

    Args:
        env_file: Custom environment files to load instead of the default hierarchy.
                  If provided, only these files will be used.
        add_debug: Whether to add a DEBUG variable automatically. Defaults to False.
    """

    # File name to look for in directories
    ENV_FILENAME: ClassVar[str] = ".env"

    env_file: list[Path] | Path | str | None = field(default_factory=list)
    add_debug: bool = False

    logger: Logger = field(init=False)

    vars: dict[str, PolyVar] = field(default_factory=dict)
    values: dict[str, Any] = field(default_factory=dict)
    attr_names: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize with default environment variables."""
        # If env_file is a string or list, convert to Path objects
        self.env_file = (
            Path(self.env_file)
            if isinstance(self.env_file, str)
            else [Path(f) for f in self.env_file]
            if isinstance(self.env_file, list)
            else self.env_file
        )

        # Check the environment variable for debug mode
        env_debug = self.validate_bool(os.environ.get("ENV_DEBUG", "0"))

        # Set up the logger
        self.logger = PolyLog.get_logger(level="DEBUG" if env_debug else "INFO")

        # Load environment variables from files
        self._load_env_files()

        if self.add_debug and "DEBUG" not in self.vars:
            self.add_debug_var()

    def _load_env_files(self) -> None:
        """Load environment variables from specified files, including parent directories."""
        if not self.env_file:  # If no specific files are provided, use hierarchical loading
            env_files = []

            # Add .env files from parent directories (from root toward current dir)
            current_dir = Path.cwd().absolute()
            parent_dirs = list(current_dir.parents)

            # Limit how far up we go - stop at the user's home directory
            home_dir = Path.home()
            if home_dir in parent_dirs:
                # Only include parents up to and including home directory
                parent_dirs = parent_dirs[: parent_dirs.index(home_dir) + 1]

            # Add parent directories in reverse order (from furthest to closest)
            for parent in reversed(parent_dirs):
                parent_env = parent / self.ENV_FILENAME
                env_files.append(parent_env)

            # Add current directory's .env
            env_files.append(Path(self.ENV_FILENAME))

            # Add ~/.env explicitly to ensure it's always checked
            home_env = Path(f"~/{self.ENV_FILENAME}").expanduser()
            if home_env not in env_files:
                env_files.append(home_env)

            self.env_file = env_files
            self.logger.debug("Using hierarchical env files: %s", [str(f) for f in self.env_file])
        else:  # Custom files were specified, so use only those
            self.logger.debug(
                "Using custom env files: %s",
                [str(self.env_file)]
                if isinstance(self.env_file, (str, Path))
                else [str(f) for f in self.env_file],
            )

        env_files = (
            [Path(self.env_file)] if isinstance(self.env_file, str | Path) else self.env_file
        )

        # Track which variables came from which files for potential debugging
        loaded_from = {}

        for file in env_files:
            full_path = Path(file).expanduser()
            abs_path = full_path.absolute()

            self.logger.debug("Checking for env file: %s", abs_path)
            if full_path.exists():
                self.logger.debug("Loading env from: %s", abs_path)
                # Track which variables were loaded from this file
                before_keys = set(os.environ.keys())
                load_dotenv(str(full_path), override=True)
                after_keys = set(os.environ.keys())

                new_keys = after_keys - before_keys
                for key in new_keys:
                    loaded_from[key] = str(abs_path)

                self.logger.debug("Env load from %s: %s variables loaded", abs_path, len(new_keys))
            else:
                self.logger.debug("No env file found: %s", abs_path)

        if loaded_from and self.logger.isEnabledFor(10):  # DEBUG level
            self.logger.debug("Environment variables loaded from:")
            for var, source in sorted(loaded_from.items()):
                self.logger.debug("  %s: %s", var, source)

    def refresh(self) -> None:
        """Reload environment variables from files and clear cached values."""
        self._load_env_files()
        self.values.clear()
        self.logger.info("PolyEnv environment flushed and reloaded.")

    def validate_all(self) -> None:
        """Validate all registered environment variables at once.

        Raises:
            ValueError: With a summary of all missing or invalid variables.
        """
        errors = []

        for name in self.vars:
            try:
                self.get(name)
            except (ValueError, KeyError) as e:
                errors.append(f"{name}: {e}")

        if errors:
            msg = "Environment validation failed:\n- " + "\n- ".join(errors)
            raise ValueError(msg)

    def add_var(
        self,
        name: str,
        attr_name: str | None = None,
        required: bool = True,
        default: Any = "",
        var_type: Callable[[str], Any] = str,
        description: str = "",
        secret: bool = False,
    ) -> None:
        """Add an environment variable to track.

        Args:
            name: Environment variable name (e.g. 'SSH_PASSPHRASE').
            attr_name: Optional attribute name override (e.g. 'ssh_pass').
            required: Whether this variable is required.
            default: Default value if not required.
            var_type: Type to convert value to (e.g. int, float, str, bool).
            description: Human-readable description.
            secret: Whether to mask the value in logs.
        """
        # If a default is provided or variable is not required, ensure consistency
        if not required:
            # Ensure non-required vars have a default (empty string is fine)
            if default is None:
                default = ""
        elif default not in {None, ""}:
            # If required=True but a non-empty default is provided, that's a logical conflict
            self.logger.warning(
                "Variable %s marked as required but has default value. Setting required=False.",
                name,
            )
            required = False

        # Use provided attr_name or convert ENV_VAR_NAME to env_var_name
        attr = attr_name or name.lower()
        self.attr_names[attr] = name

        self.vars[name] = PolyVar(
            name=name.upper(),
            required=required,
            default=default,
            var_type=var_type,
            description=description,
            secret=secret,
        )

    def add_vars(self, *vars: PolyVar) -> None:  # noqa: A002
        """Add multiple environment variables at once.

        Args:
            *vars: EnvVar instances to add
        """
        for var in vars:
            self.add_var(
                name=var.name,
                required=var.required,
                default=var.default,
                var_type=var.var_type,
                description=var.description,
                secret=var.secret,
            )

    def add_bool(
        self,
        name: str,
        attr_name: str | None = None,
        required: bool = False,
        default: bool = False,
        description: str = "",
    ) -> None:
        """Add a boolean environment variable with smart string conversion.

        This is a convenience wrapper around add_var() specifically for boolean values.
        It handles various string representations of boolean values in a case-insensitive way.

        Valid input values (case-insensitive):
        - True: 'true', '1', 'yes', 'on', 't', 'y'
        - False: 'false', '0', 'no', 'off', 'f', 'n'

        Args:
            name: Environment variable name (e.g. "ENABLE_FEATURE")
            attr_name: Optional attribute name override (e.g. "feature_enabled")
            required: Whether this variable is required.
            default: Default boolean value if not required.
            description: Human-readable description.
        """
        self.add_var(
            name=name,
            attr_name=attr_name,
            required=required,
            default=default,
            var_type=self.validate_bool,
            description=description,
            secret=False,
        )

    def add_debug_var(
        self,
        name: str = "DEBUG",
        default: bool = False,
        description: str = "Enable debug mode",
    ) -> None:
        """Simple shortcut to add a consistent boolean DEBUG environment variable."""
        self.add_bool(name=name, required=False, default=default, description=description)

    @property
    def debug_enabled(self) -> bool:
        """Check if debug mode is enabled via environment variables."""
        # First check if DEBUG is registered
        if "DEBUG" in self.vars:
            try:
                return bool(self.get("DEBUG"))
            except (KeyError, ValueError):
                pass

        # Fall back to direct environment check for runtime overrides
        debug_str = os.environ.get("DEBUG", "").lower()
        return debug_str in {"true", "1", "yes", "y", "on", "t"}

    @property
    def log_level(self) -> str:
        """Get the appropriate log level based on debug settings."""
        return "DEBUG" if self.debug_enabled else "INFO"

    def get(self, name: str, default: Any | None = None) -> Any:
        """Get the value of an environment variable.

        Args:
            name: The environment variable name
            default: Override default value (takes precedence over registered default)

        Raises:
            KeyError: If the given name is unknown.
            ValueError: If the required variable is missing or has an invalid value.
        """
        if name not in self.vars:
            msg = f"Unknown environment variable: {name}"
            raise KeyError(msg)

        # Return the cached value first if we have it
        if name in self.values:
            return self.values[name]

        var = self.vars[name]

        # Try to get the value from the environment
        value = os.environ.get(name)

        # Determine the final value using clear priority order
        if value is not None:
            # Environment value exists, use it
            pass
        elif default is not None:
            # Use the override default from this method call
            value = default
        elif not var.required and var.default is not None:
            # Use the registered default for non-required vars
            value = var.default
        elif var.required:
            # Required var with no value
            desc = f" ({var.description})" if var.description else ""
            msg = f"Required environment variable {name} not set{desc}"
            raise ValueError(msg)
        else:
            # Non-required var with no default
            return None

        # Convert the value
        try:
            converted = var.var_type(value)
            self.values[name] = converted
            return converted
        except Exception as e:
            msg = f"Invalid value for {name}: {e!s}"
            raise ValueError(msg) from e

    def __getattr__(self, name: str) -> Any:
        """Allow accessing variables as attributes.

        Raises:
            AttributeError: If the given name is unknown.
        """
        if name in self.attr_names:
            return self.get(self.attr_names[name])
        msg = f"'{self.__class__.__name__}' has no attribute '{name}'"
        raise AttributeError(msg)

    def get_all_values(self, include_secrets: bool = False) -> dict[str, Any]:
        """Get all environment variable values.

        Args:
            include_secrets: Whether to include variables marked as secret.

        Returns:
            Dictionary of variable names to their values.
        """
        result = {}
        for name, var in self.vars.items():
            if var.secret and not include_secrets:
                continue
            try:
                result[name] = self.get(name)
            except (ValueError, KeyError):
                result[name] = None
        return result

    @staticmethod
    def validate_bool(value: str) -> bool:
        """Convert various string representations to boolean values.

        Handles common truthy/falsey string values in a case-insensitive way:
            - True values: 'true', '1', 'yes', 'on', 't', 'y'
            - False values: 'false', '0', 'no', 'off', 'f', 'n'

        Raises:
            ValueError: If the string cannot be converted to a boolean.
        """
        value = str(value).lower().strip()

        true_values = {"true", "1", "yes", "on", "t", "y"}
        false_values = {"false", "0", "no", "off", "f", "n"}

        if value in true_values:
            return True
        if value in false_values:
            return False

        msg = (
            f"Cannot convert '{value}' to boolean. "
            f"Valid true values: {', '.join(sorted(true_values))}. "
            f"Valid false values: {', '.join(sorted(false_values))}."
        )
        raise ValueError(msg)
