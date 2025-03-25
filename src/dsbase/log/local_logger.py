"""Classes for setting up and formatting loggers.

LocalLogger and related classes provide methods for setting up a logger with a console handler,
defining console color codes for use in the formatter to colorize messages by log level, and more.
"""

from __future__ import annotations

import logging
import logging.config
from logging import Logger
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING

from dsbase.log.log_formatters import CustomFormatter, FileFormatter
from dsbase.log.log_metadata import LogLevel
from dsbase.util import Singleton

if TYPE_CHECKING:
    from dsbase.env import EnvManager


class LocalLogger(metaclass=Singleton):
    """Set up an easy local logger with a console handler.

    Logs at DEBUG level by default, but can be set to any level using the log_level parameter. Uses
    a custom formatter that includes the time, logger name, function name, and log message.

    Usage:
        from dsbase import LocalLogger
        logger = LocalLogger().get_logger(self.__class__.__name__)
        logger = LocalLogger().get_logger("MyClassLogger", advanced=True)
    """

    def get_logger(
        self,
        logger_name: str | None = None,
        level: int | str = "INFO",
        simple: bool = False,
        show_context: bool = False,
        color: bool = True,
        log_file: Path | None = None,
        env: EnvManager | None = None,
    ) -> Logger:
        """Set up a logger with the given name and log level.

        Args:
            logger_name: The name of the logger. If None, the class or module name is used.
            level: The log level. Defaults to 'INFO'.
            simple: Use simple format that displays only the log message itself. Defaults to False.
            show_context: Show the class and function name in the log message. Defaults to False.
            color: Use color in the log output. Defaults to True.
            log_file: Path to a desired log file. Defaults to None, which means no file logging.
            env: An optional EnvManager instance to get the log level from.
        """
        logger_name = LocalLogger().get_logger_name(logger_name)
        logger = logging.getLogger(logger_name)

        # Use the log level from EnvManager if we have it, unless we're already at DEBUG level
        if env is not None and level != "DEBUG":
            level = env.log_level

        if not logger.handlers:
            log_level = LogLevel.get_level(level)
            logger.setLevel(log_level)

            log_formatter = CustomFormatter(simple=simple, color=color, show_context=show_context)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_formatter)
            console_handler.setLevel(log_level)
            logger.addHandler(console_handler)

            if log_file:
                self.add_file_handler(logger, log_file)

            logger.propagate = False

        return logger

    @staticmethod
    def get_logger_name(logger_name: str | None = None) -> str:
        """Generate a logger identifier based on the provided parameters and calling context."""
        if logger_name is not None:
            return logger_name

        import inspect

        # Try to get the calling frame
        frame = inspect.currentframe()
        if frame is not None:
            frame = frame.f_back  # get_logger's frame
            if frame is not None:
                frame = frame.f_back  # get_logger's caller's frame

        # If we have a valid frame, try to identify it
        if frame is not None:
            # Try to get class name first
            if "self" in frame.f_locals:
                return frame.f_locals["self"].__class__.__name__
            if "cls" in frame.f_locals:
                return frame.f_locals["cls"].__name__

            # Get the module name if we can't get the class name
            module = inspect.getmodule(frame)
            if module is not None and hasattr(module, "__name__"):
                return module.__name__.split(".")[-1]

            # Get the filename if we can't get the module name
            filename = frame.f_code.co_filename
            if filename:
                base_filename = Path(filename).name
                return Path(base_filename).stem

        # If we really can't find our place in the universe
        return "unknown"

    def add_file_handler(self, logger: Logger, log_file: Path) -> None:
        """Add a file handler to the given logger.

        Args:
            logger: The logger to add the file handler to.
            log_file: The path to the log file.
        """
        formatter = FileFormatter()
        log_dir = Path(log_file).parent

        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)

        if not log_file.is_file():
            log_file.touch()

        file_handler = RotatingFileHandler(log_file, maxBytes=512 * 1024)
        file_handler.setFormatter(formatter)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
