from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from dsbase.time.time import Time

if TYPE_CHECKING:
    from logging import Logger


@dataclass
class TimeAwareLogger:
    """A logger class that formats datetime objects into human-readable strings."""

    logger: Logger

    def __getattr__(self, item: Any) -> Any:
        """Delegate attribute access to the underlying logger object.

        This handles cases where the logger's method is called directly on this class instance.
        """
        return getattr(self.logger, item)

    @staticmethod
    def _format_args(*args: Any) -> list[Any]:
        return [Time.get_pretty_time(arg) if isinstance(arg, datetime) else arg for arg in args]

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message with time formatted arguments."""
        formatted_args = self._format_args(*args)
        kwargs.setdefault("stacklevel", 2)
        self.logger.debug(msg, *formatted_args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message with time formatted arguments."""
        formatted_args = self._format_args(*args)
        kwargs.setdefault("stacklevel", 2)
        self.logger.info(msg, *formatted_args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message with time formatted arguments."""
        formatted_args = self._format_args(*args)
        kwargs.setdefault("stacklevel", 2)
        self.logger.warning(msg, *formatted_args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message with time formatted arguments."""
        formatted_args = self._format_args(*args)
        kwargs.setdefault("stacklevel", 2)
        self.logger.error(msg, *formatted_args, **kwargs)
