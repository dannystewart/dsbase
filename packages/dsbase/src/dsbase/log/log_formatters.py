from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from logging import Formatter, LogRecord
from zoneinfo import ZoneInfo

from dsbase.log.log_metadata import LogColors, LogLevel


@dataclass
class CustomFormatter(Formatter):
    """Custom log formatter supporting both basic and advanced formats."""

    simple: bool = False
    show_context: bool = False
    color: bool = True

    def __post_init__(self):
        super().__init__()

    def formatTime(self, record: LogRecord, datefmt: str | None = None) -> str:  # noqa
        """Format the time in a log record."""
        tz = ZoneInfo(os.getenv("TZ", "America/New_York"))
        ct = datetime.fromtimestamp(record.created, tz=tz)
        return ct.strftime(datefmt) if datefmt else ct.isoformat()

    def format(self, record: LogRecord) -> str:
        """Format the log record based on the formatter style."""
        if self.color:
            level_color = LogLevel.get_color(record.levelname)
            reset = LogColors.RESET
            bold = LogColors.BOLD
            gray = LogColors.GRAY
            blue = LogColors.BLUE
            cyan = LogColors.CYAN
        else:
            level_color = reset = bold = gray = blue = cyan = ""

        # Add the timestamp to the record
        record.asctime = self.formatTime(record, "%I:%M:%S %p")

        if self.simple:  # Messages above INFO show in bold
            bold = "" if record.levelname in {"DEBUG", "INFO"} else bold
            return f"{reset}{bold}{level_color}{record.getMessage()}{reset}"

        # Format the timestamp
        timestamp = f"{reset}{gray}{record.asctime}{reset} "

        # Format the log level text
        level_texts = {
            "CRITICAL": "[CRITICAL]",
            "ERROR": "[ERROR]",
            "WARNING": "[WARN]",
            "INFO": "[INFO]",
            "DEBUG": "[DEBUG]",
        }
        level_text = level_texts.get(record.levelname, "")
        log_level = f"{bold}{level_color}{level_text}{reset}"

        # Add level color to reset if above INFO
        if record.levelname not in {"DEBUG", "INFO"}:
            reset = f"{level_color}{reset}"

        # Format the function color and name
        class_name = f" {blue}{record.name}:{reset} " if self.show_context else ""
        function = f"{cyan}{record.funcName}: " if self.show_context else " "

        # Format the message and return the formatted message
        message = f"{level_color}{record.getMessage()}{reset}"
        return f"{timestamp}{log_level}{class_name}{function}{message}"


@dataclass
class FileFormatter(Formatter):
    """Formatter class for file log messages."""

    def format(self, record: LogRecord) -> str:
        """Format a log record for file output."""
        record.asctime = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        return f"[{record.asctime}] [{record.levelname}] {record.name}: {record.funcName}: {record.getMessage()}"
