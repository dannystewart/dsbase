from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from dotenv import load_dotenv

from dsbase.log import LocalLogger
from dsbase.util import Singleton

if TYPE_CHECKING:
    from collections.abc import Callable
    from logging import Logger

T = TypeVar("T")


@dataclass
class EnvVar:
    """Represents an environment variable with validation and type conversion.

    Args:
        name: Environment variable name.
        required: Whether this variable is required.
        default: Default value if not required.
        var_type: Type to convert value to (e.g., int, float, str, bool).
        description: Human-readable description of the variable.
        secret: Whether to mask the value in logs.

    NOTE: var_type is used as a converter function to wrap the provided data. This means it can also
          use custom conversion functions to get other types of data with convert(value) -> Any.
    """

    name: str
    required: bool = False
    default: Any = None
    var_type: Callable[[str], Any] = str
    description: str = ""
    secret: bool = False

    def __post_init__(self) -> None:
        if not self.required and self.default is None:
            msg = f"Non-required variable {self.name} must have a default value"
            raise ValueError(msg)


@dataclass
class EnvManager(metaclass=Singleton):
    """Manage environment variables in a friendly way."""

    DEFAULT_ENV_FILES: ClassVar[list[Path]] = [Path(".env"), Path("~/.env").expanduser()]

    env_file: list[Path] | Path | str | None = field(default_factory=list)
    vars: dict[str, EnvVar] = field(default_factory=dict)
    values: dict[str, Any] = field(default_factory=dict)
    attr_names: dict[str, str] = field(default_factory=dict)

    logger: Logger = field(init=False)

    def __post_init__(self):
        """Initialize with default environment variables."""
        self.logger = LocalLogger().get_logger(level=self.log_level)
        self._load_env_files()

    def _load_env_files(self) -> None:
        """Load environment variables from specified files."""
        if not self.env_file:
            self.env_file = self.DEFAULT_ENV_FILES
            self.logger.debug("Using default env files: %s", [str(f) for f in self.env_file])

        env_files = [self.env_file] if isinstance(self.env_file, str | Path) else self.env_file
        for file in env_files:
            full_path = Path(file).expanduser() if isinstance(file, str) else file.expanduser()

            local_dir = full_path == self.DEFAULT_ENV_FILES[0]
            abs_path = full_path.absolute()
            path_str = "local env" if local_dir else "env"

            self.logger.debug("Checking for %s: %s", path_str, abs_path)
            if full_path.exists():
                self.logger.debug("Loading env from: %s", abs_path)
                result = load_dotenv(str(full_path), override=True)
                self.logger.debug("Env load result: %s", "Success" if result else "No changes")
            else:
                self.logger.debug("No %s found: %s", path_str, abs_path)

    def refresh(self) -> None:
        """Reload environment variables from files and clear cached values."""
        self._load_env_files()
        self.values.clear()
        self.logger.info("EnvManager environment flushed and reloaded.")

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

        self.vars[name] = EnvVar(
            name=name.upper(),
            required=required,
            default=default,
            var_type=var_type,
            description=description,
            secret=secret,
        )

    def add_vars(self, *vars: EnvVar) -> None:  # noqa: A002
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

    def get(self, name: str, default: Any = None) -> Any:
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
