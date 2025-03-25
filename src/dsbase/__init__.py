# ruff: noqa: D212, D415
"""
# DSBase

Danny Stewart's Python Utility Library, or **DSBase**, provides a collection of utility functions
and classes to simplify common Python programming tasks.

## Installation

```bash
pip install dsbase
```

## Core Features

- **Text Processing**: Color formatting, text manipulation, and pattern matching
- **File Operations**: Simplified file handling, searching, and management
- **Logging**: Customized logging setup with sensible defaults
- **Version Management**: Tools for checking and comparing package versions

See the individual module documentation for more detailed API information.
"""

from __future__ import annotations

from dsbase.env import EnvManager
from dsbase.files import FileManager
from dsbase.log import LocalLogger, TimeAwareLogger
from dsbase.media import MediaManager
from dsbase.paths import PathKeeper
from dsbase.text import Text
from dsbase.time import Time
from dsbase.util import ArgParser, Singleton
