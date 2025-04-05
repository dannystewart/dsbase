# PolyLog

**The logical choice for Python logging.** 🖖

PolyLog is a powerful, colorful, and intuitive logging library for Python that makes beautiful logs easy.

## Features

- **Color-coded log levels:** Instantly identify log importance with intuitive colors.
- **Flexible formatting:** Choose between detailed or simple log formats.
- **Smart context detection:** Automatically detects logger names from classes and modules.
- **Time-aware logging:** Formats datetime objects into human-readable strings.
- **File logging:** Easily add rotating file handlers with sensible defaults.
- **Thread-safe:** Designed for reliable logging in multi-threaded applications.

## Installation

```bash
pip install polylog
```

## Quick Start

```python
from polylog import PolyLog

# Create a basic logger
logger = PolyLog.get_logger("MyApp")
logger.info("Application started")
logger.warning("Something seems off...")
logger.error("An error occurred!")

# With automatic name detection
class MyClass:
    def __init__(self):
        self.logger = PolyLog.get_logger()  # Automatically uses "MyClass" as the logger name
        self.logger.info("MyClass initialized")

# Simple format (just the message)
simple_logger = PolyLog.get_logger("SimpleLogger", simple=True)
simple_logger.info("This message appears without timestamp or context")

# With context information
context_logger = PolyLog.get_logger("ContextLogger", show_context=True)
context_logger.info("This message shows which function called it")

# Time-aware logging
from datetime import datetime
time_logger = PolyLog.get_logger("TimeLogger", time_aware=True)
time_logger.info("Event occurred at %s", datetime.now())  # Formats the datetime nicely

# File logging
from pathlib import Path
file_logger = PolyLog.get_logger("FileLogger", log_file=Path("app.log"))
file_logger.info("This message goes to both console and file")
```

## Advanced Usage

### Customizing Log Format

```python
# Different log level
logger = PolyLog.get_logger("DEBUG_LOGGER", level="DEBUG")
logger.debug("This debug message will be visible")

# Turning off colors (useful for CI/CD environments)
no_color_logger = PolyLog.get_logger("NoColor", color=False)
```

### TimeAwareLogger

The TimeAwareLogger automatically formats datetime objects in log messages:

```python
from datetime import datetime, timedelta
from polylog import PolyLog

logger = PolyLog.get_logger("TimeDemo", time_aware=True)

now = datetime.now()
yesterday = now - timedelta(days=1)
next_week = now + timedelta(days=7)

logger.info("Current time: %s", now)                 # "Current time: today at 2:30 PM"
logger.info("Yesterday was: %s", yesterday)          # "Yesterday was: yesterday at 2:30 PM"
logger.info("Meeting scheduled for: %s", next_week)  # "Meeting scheduled for: Monday at 2:30 PM"
```

## Types and Constants

PolyLog provides several types and constants that you can import directly for type-safe logging:

```python
from polylog import PolyLog
from polylog.types import LogLevel, LogColors

# Use enum values for type safety
logger = PolyLog.get_logger(level=LogLevel.DEBUG)

# Log with specific levels
logger.log(LogLevel.get_level(LogLevel.WARNING), "This is a warning")

# Check log levels in code
if current_level == LogLevel.ERROR:
    # Handle error case
    pass

# Access color constants if needed for custom formatting
print(f"{LogColors.RED}This text is red{LogColors.RESET}")
```

### Available Types

- **LogLevel**: Enum for log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
- **LogColors**: Enum for ANSI color codes used in terminal output

This provides better IDE support for autocompletion and type checking compared to string literals.
