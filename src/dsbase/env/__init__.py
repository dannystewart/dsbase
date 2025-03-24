# ruff: noqa: D212, D415

"""
# EnvManager

EnvManager is a utility class that manages environment variables in a friendly way.

This class allows you to add environment variables with type conversion, validation, and secret
masking. Variables can be accessed as attributes. Defaults to loading environment variables from
`.env` and `~/.env`, but also uses the current environment and allows specifying custom files.

## Usage

```python
# Basic usage with default values of .env and ~/.env
env_man = EnvManager()

# Custom .env file
env_man = EnvManager(env_file="~/.env_man.local")

# Multiple .env files (processed in order, so later files take precedence)
env_man = EnvManager(env_file=["~/.env", "~/.env_man.local"])

# Add variables with automatic attribute names
env_man.add_var(
    "SSH_PASSPHRASE",  # Access as env_man.ssh_passphrase
    description="SSH key passphrase",
    secret=True,
)

# Add variables with custom attribute names
env_man.add_var(
    "MYSQL_PASSWORD",
    attr_name="db_password",  # Access as env_man.db_password
    description="MySQL password for upload user",
    secret=True,
)

# Add boolean variable with smart string conversion
env_man.add_bool("DEBUG_MODE", description="Enable debug mode")

# Add a standard debug flag
env_man.add_debug_var()

# Validate all variables - raises ValueError if any are invalid
try:
    env_man.validate_all()
except ValueError as e:
    print(f"Environment validation failed: {e}")
    # Handle error appropriately

# Use variables through attributes
ssh_pass = env_man.ssh_passphrase
db_pass = env_man.db_password

# Or use traditional get() method (with optional default value)
debug_mode = env_man.get("DEBUG_MODE", False)

# Get all values (with secrets masked)
all_values = env_man.get_all_values()
print(all_values)

# Check if debug is enabled and get appropriate log level
if env_man.debug_enabled:
    print(f"Debug is enabled, log level: {env_man.log_level}")
```

## Features

- Type conversion and validation
- Secret masking for sensitive values
- Attribute-style access to variables
- Smart boolean conversion
- Default value handling
- Multiple .env file support
- Debug mode detection
"""

from __future__ import annotations

from .env_manager import EnvManager
