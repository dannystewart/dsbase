# PolyEnv

PolyEnv is an environment variable manager for Python applications. It handles loading from multiple `.env` files, type conversion, validation, and provides an elegant interface for accessing your environment configuration.

## Features

- **Hierarchical loading** from multiple `.env` files with smart precedence rules.
- **Type conversion** to automatically convert environment strings to Python types.
- **Validation** to ensure required variables are present and correctly formatted.
- **Attribute access** for clean, IDE-friendly environment variable usage.
- **Secret masking** to prevent sensitive values from appearing in logs.
- **Smart boolean parsing** that understands various truthy/falsey string formats.
- **Singleton pattern** ensuring consistent environment state throughout your application.

### Why PolyEnv?

- **Cleaner code**: Access environment variables with proper IDE autocompletion
- **Type safety**: No more manual type conversion or validation
- **Hierarchical configuration**: Different settings for development, staging, and production
- **Explicit requirements**: Document which environment variables your application needs
- **Fail-fast validation**: Detect missing or invalid configuration early

## Quick Start

```python
from polykit.env import PolyEnv

# Create the environment manager (uses singleton pattern)
env = PolyEnv()

# Register environment variables
env.add_var("API_KEY", required=True, description="External API authentication key", secret=True)
env.add_var("MAX_CONNECTIONS", var_type=int, default=5, description="Maximum connection pool size")
env.add_bool("DEBUG_MODE", default=False, description="Enable verbose debug output")

# Access variables as attributes
api_key = env.api_key
max_conn = env.max_connections
is_debug = env.debug_mode

# Or use the get() method with optional runtime defaults
timeout = env.get("TIMEOUT_SECONDS", default=30)

# Validate all variables at once (e.g., during application startup)
try:
    env.validate_all()
    print("Environment validation successful!")
except ValueError as e:
    print(f"Environment configuration error: {e}")
    exit(1)
```

## Environment Loading Strategy

PolyEnv uses a sophisticated hierarchical approach to loading environment variables:

1. Loads from `.env` files in parent directories (up to user's home directory)
2. Loads from the current directory's `.env` file
3. Loads from `~/.env` (user's home directory)
4. Uses current environment variables
5. Allows specifying custom files that override all of the above

This means more specific configurations (closer to the current directory) override broader ones. For example, if you have `/home/user/.env` and `/home/user/project/.env`, variables in the project-specific file will take precedence.

## Advanced Usage

### Custom Environment Files

```python
# Use a specific .env file
env = PolyEnv(env_file="~/.config/myapp/.env")

# Use multiple .env files (processed in order, later files take precedence)
env = PolyEnv(env_file=["~/.env.defaults", "~/.env.local"])
```

### Working with Secrets

```python
# Register sensitive variables
env.add_var("DB_PASSWORD", secret=True, description="Database password")
env.add_var("API_TOKEN", secret=True, description="API authentication token")

# Get all values with secrets masked
all_values = env.get_all_values()  # Secrets show as "[MASKED]"
print(all_values)

# Include secrets when needed (e.g., for debugging in secure environments)
all_values_with_secrets = env.get_all_values(include_secrets=True)
```

### Custom Type Conversion

```python
# Use built-in types
env.add_var("PORT", var_type=int, default=8080)
env.add_var("RATE_LIMIT", var_type=float, default=1.5)

# Use custom conversion functions
def parse_list(value):
    return [item.strip() for item in value.split(',')]

env.add_var("ALLOWED_ORIGINS", var_type=parse_list, default="localhost")
```

### Boolean Variables

```python
# Add a boolean with smart string conversion
env.add_bool("FEATURE_ENABLED", default=False)

# These all evaluate to True:
# FEATURE_ENABLED=true
# FEATURE_ENABLED=1
# FEATURE_ENABLED=yes
# FEATURE_ENABLED=on
# FEATURE_ENABLED=y

# These all evaluate to False:
# FEATURE_ENABLED=false
# FEATURE_ENABLED=0
# FEATURE_ENABLED=no
# FEATURE_ENABLED=off
# FEATURE_ENABLED=n
```

### Debugging

For detailed logging of PolyEnv's own operations:

```bash
# Set this environment variable before running your application
export ENV_DEBUG=1
```

Or in your code:

```python
import os
os.environ["ENV_DEBUG"] = "1"
```
