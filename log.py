"""
Classes for setting up and formatting loggers. The LocalLogger class provides a method for setting
up a logger with a console handler. The ConsoleColors class defines console color codes for use in
the formatter to colorize messages by log level.
"""

import logging
import os
from datetime import datetime
from typing import Literal

from zoneinfo import ZoneInfo

FormatterLevel = Literal["basic", "advanced"]


class LocalLogger:
    """
    Set up an easy local logger with a console handler. The level is set to INFO by default, but can
    be set to any level using the log_level parameter. The logger uses a custom formatter that
    includes the time, logger name, function name, and log message.

    Usage:
        from dsutil.log import LocalLogger
        logger = LocalLogger.setup_logger(self.__class__.__name__)
        logger = LocalLogger.setup_logger("MyClassLogger", advanced=True)
    """

    LEVEL_COLORS = {
        "DEBUG": "\033[90m",  # Gray
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[95m",  # Magenta
    }

    RESET = "\033[0m"
    BOLD = "\033[1m"
    GRAY = "\033[90m"

    @staticmethod
    def setup_logger(
        logger_name: str,
        level: int = logging.INFO,
        message_only: bool = False,
        use_color_messages: bool = True,
        show_function_name: bool = False,
    ) -> logging.Logger:
        """Set up a logger with the given name and log level."""
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

        log_formatter = LocalLogger.CustomFormatter(
            message_only=message_only,
            use_color_messages=use_color_messages,
            show_function_name=show_function_name,
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

        logger.propagate = False
        return logger

    class CustomFormatter(logging.Formatter):
        """Custom log formatter supporting both basic and advanced formats."""

        def __init__(
            self,
            message_only: bool = False,
            use_color_messages: bool = True,
            show_function_name: bool = False,
        ) -> None:
            super().__init__()
            self.basic = message_only
            self.color_messages = use_color_messages
            self.show_function = show_function_name

        def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:  # noqa
            """Format the time in a log record."""
            tz = ZoneInfo(os.getenv("TZ", "America/New_York"))
            ct = datetime.fromtimestamp(record.created, tz=tz)
            return ct.strftime(datefmt) if datefmt else ct.isoformat()

        def format(self, record: logging.LogRecord) -> str:
            """Format the log record based on the formatter style."""
            level_color = LocalLogger.LEVEL_COLORS.get(record.levelname, LocalLogger.RESET)
            reset = LocalLogger.RESET
            bold = LocalLogger.BOLD
            gray = LocalLogger.GRAY

            # Add the timestamp to the record
            record.asctime = self.formatTime(record, "%I:%M:%S %p")

            # If we're using the basic log format, return the message only
            if self.basic:
                return f"{reset}{bold}{level_color}{record.getMessage()}{reset}"

            # Format the timestamp
            timestamp = f"{reset}{gray}{record.asctime}{reset} "

            # Format the log level text
            level_texts = {
                "CRITICAL": "[CRITICAL]",
                "ERROR": "[ERROR]",
                "WARNING": "[WARN]",
                "INFO": "[INFO]",
            }
            level_text = level_texts.get(record.levelname, "")
            log_level = f"{bold}{level_color}{level_text}{reset}"

            # Format the function color and name
            func_color = f"{reset}" if self.color_messages else ""
            function = f"{func_color}{record.funcName}: " if self.show_function else ""

            # Format the message color and return the formatted message
            msg_color = f"{level_color}" if self.color_messages else ""
            message = f"{msg_color}{record.getMessage()}{reset}"
            return f"{timestamp}{log_level} {function}{message}"
