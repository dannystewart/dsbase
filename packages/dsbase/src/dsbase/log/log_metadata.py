from __future__ import annotations

import logging
import logging.config
from enum import StrEnum


class LogLevel(StrEnum):
    """Available logging levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    @classmethod
    def get_level(cls, level: int | str | LogLevel) -> int:
        """Convert any level format to a logging level integer."""
        if isinstance(level, int):
            return level
        if isinstance(level, cls):
            return LOG_LEVELS[level]
        return LOG_LEVELS[cls(level.lower())]

    @classmethod
    def get_color(cls, levelname: str) -> str:
        """Get the color code for a log level name."""
        try:
            return LEVEL_COLORS[cls(levelname.lower())].value
        except ValueError:
            return LogColors.RESET.value


LOG_LEVELS: dict[LogLevel, int] = {
    LogLevel.DEBUG: logging.DEBUG,
    LogLevel.INFO: logging.INFO,
    LogLevel.WARNING: logging.WARNING,
    LogLevel.ERROR: logging.ERROR,
    LogLevel.CRITICAL: logging.CRITICAL,
}


class LogColors(StrEnum):
    """Available types of log formatting."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    WHITE = "\033[37m"
    BLACK = "\033[30m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"
    GREEN = "\033[32m"
    MAGENTA = "\033[95m"
    PURPLE = "\033[35m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_WHITE = "\033[97m"
    BRIGHT_YELLOW = "\033[93m"


LEVEL_COLORS: dict[LogLevel, LogColors] = {
    LogLevel.DEBUG: LogColors.GRAY,
    LogLevel.INFO: LogColors.GREEN,
    LogLevel.WARNING: LogColors.YELLOW,
    LogLevel.ERROR: LogColors.RED,
    LogLevel.CRITICAL: LogColors.MAGENTA,
}
