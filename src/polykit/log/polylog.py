"""Classes for setting up and formatting loggers.

PolyLog and related classes provide methods for setting up a logger with a console handler,
defining console color codes for use in the formatter to colorize messages by log level, and more.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from polykit.core.singleton import Singleton
from polykit.log.formatters import CustomFormatter, FileFormatter
from polykit.log.types import LogLevel


class PolyLog(metaclass=Singleton):
    """A powerful, colorful logger for Python applications. The logical choice for Python logging.

    PolyLog provides easy configuration of Python's standard logging with sensible defaults and
    features like automatic context detection, color-coded output, and datetime formatting.

    Usage:
        from logician import PolyLog

        # Basic usage with automatic name detection
        logger = PolyLog.get_logger()
        logger.info("Application started.")

        # With explicit name and options
        logger = PolyLog.get_logger("MyComponent", level="DEBUG", show_context=True)

        # With datetime formatting
        from datetime import datetime
        time_logger = PolyLog.get_logger(time_aware=True)
        time_logger.info("Event occurred at %s", datetime.now())  # Formats datetime nicely
    """

    @classmethod
    def get_logger(
        cls,
        logger_name: str | None = None,
        level: int | str = "INFO",
        simple: bool = False,
        show_context: bool = False,
        color: bool = True,
        log_file: Path | None = None,
        time_aware: bool = False,
    ) -> logging.Logger:
        """Get a configured logger instance.

        Args:
            logger_name: The name of the logger. If None, automatically determined from the calling
                         class, module, or file name.
            level: The log level as string ("DEBUG", "INFO", etc.) or a logging constant.
                   Defaults to "INFO".
            simple: If True, use a simplified format that shows only the message. Defaults to False.
            show_context: If True, include the function/method name in log messages.
                          Defaults to False.
            color: If True, use color-coded output based on log level. Defaults to True.
            log_file: Optional path to a log file. If provided, logs will be written to this file in
                      addition to the console. Defaults to None, which means no file logging.
            time_aware: If True, returns a TimeAwareLogger that automatically formats datetime
                        objects in log messages. Defaults to False.

        Returns:
            A configured standard Logger or TimeAwareLogger instance.
        """
        logger_name = PolyLog._get_logger_name(logger_name)
        logger = logging.getLogger(logger_name)

        if not logger.handlers:
            log_level = LogLevel.get_level(level)
            logger.setLevel(log_level)

            log_formatter = CustomFormatter(simple=simple, color=color, show_context=show_context)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_formatter)
            console_handler.setLevel(log_level)
            logger.addHandler(console_handler)

            if log_file:
                PolyLog._add_file_handler(logger, log_file)

            logger.propagate = False

        if time_aware:
            from polykit.log.time_aware import TimeAwareLogger

            return TimeAwareLogger(logger)

        return logger

    @staticmethod
    def _get_logger_name(logger_name: str | None = None) -> str:
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

    @staticmethod
    def _add_file_handler(logger: logging.Logger, log_file: Path) -> None:
        """Add a file handler to the given logger."""
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
