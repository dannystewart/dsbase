"""# PolyLog

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
from polylog import Logger

# Create a basic logger
logger = Logger("MyApp")
logger.info("Application started")
logger.warning("Something seems off...")
logger.error("An error occurred!")

# With automatic name detection
class MyClass:
    def __init__(self):
        self.logger = Logger()  # Automatically uses "MyClass" as the logger name
        self.logger.info("MyClass initialized")

# Simple format (just the message)
simple_logger = Logger("SimpleLogger", simple=True)
simple_logger.info("This message appears without timestamp or context")

# With context information
context_logger = Logger("ContextLogger", show_context=True)
context_logger.info("This message shows which function called it")

# Time-aware logging
from datetime import datetime
time_logger = Logger("TimeLogger", time_aware=True)
time_logger.info("Event occurred at %s", datetime.now())  # Formats the datetime nicely

# File logging
from pathlib import Path
file_logger = Logger("FileLogger", log_file=Path("app.log"))
file_logger.info("This message goes to both console and file")
```

## Advanced Usage

### Customizing Log Format

```python
# Different log level
logger = Logger("DEBUG_LOGGER", level="DEBUG")
logger.debug("This debug message will be visible")

# Turning off colors (useful for CI/CD environments)
no_color_logger = Logger("NoColor", color=False)
```

### TimeAwareLogger

The TimeAwareLogger automatically formats datetime objects in log messages:

```python
from datetime import datetime, timedelta
from polylog import Logger

logger = Logger("TimeDemo", time_aware=True)

now = datetime.now()
yesterday = now - timedelta(days=1)
next_week = now + timedelta(days=7)

logger.info("Current time: %s", now)  # "Current time: today at 2:30 PM"
logger.info("Yesterday was: %s", yesterday)  # "Yesterday was: yesterday at 2:30 PM"
logger.info("Meeting scheduled for: %s", next_week)  # "Meeting scheduled for: Monday at 2:30 PM"
```
"""  # noqa: D415, W505

from __future__ import annotations

from .polylog import PolyLog
from .time_aware import TimeAwareLogger
