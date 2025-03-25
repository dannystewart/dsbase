from __future__ import annotations

import functools
import inspect
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])
C = TypeVar("C", bound=type[Any])


def deprecated(reason: str = "") -> Callable[[F | C], F | C]:
    """Mark a function or class as deprecated by emitting a warning when used."""

    def decorator(obj: F | C) -> F | C:
        """Decorate a function or class with a warning message."""
        message = f"{obj.__name__} is deprecated and will be removed in the future. {reason}"
        if isinstance(obj, type):
            return _decorate_class(obj, message, DeprecationWarning)  # type: ignore
        return _decorate_function(obj, message, DeprecationWarning)  # type: ignore

    return decorator


def not_yet_implemented(reason: str = "") -> Callable[[F | C], F | C]:
    """Mark a function or class as not yet implemented by raising a NotImplementedError."""

    def decorator(obj: F | C) -> F | C:
        """Decorate a function or class with a warning message."""
        message = f"{obj.__name__} is not yet implemented and cannot be used. {reason}"
        if isinstance(obj, type):
            return _decorate_class(obj, message, UserWarning)  # type: ignore
        return _decorate_function(obj, message, UserWarning)  # type: ignore

    return decorator


def _decorate_function(
    func: Callable[..., Any], message: str, category: type[Warning]
) -> Callable[..., Any]:
    """Decorate a function with a warning message and optional category."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Log a message and emit a warning."""
        frame = inspect.currentframe().f_back
        filename = frame.f_code.co_filename
        line_num = frame.f_lineno
        function = frame.f_code.co_name

        _log_and_warn(message, category, filename, line_num, function)

        if category is UserWarning:
            raise NotImplementedError(message)
        return func(*args, **kwargs)

    return wrapper


def _decorate_class[T](cls: type[T], message: str, warn_type: type[Warning]) -> type[T]:
    """Decorate a class with a warning message and optional category."""

    orig_init = cls.__init__

    @functools.wraps(orig_init)
    def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
        """Log a message and emit a warning."""
        frame = inspect.currentframe().f_back
        filename = frame.f_code.co_filename
        line_num = frame.f_lineno
        function = frame.f_code.co_name

        _log_and_warn(message, warn_type, filename, line_num, function)

        if warn_type is UserWarning:
            raise NotImplementedError(message)
        orig_init(self, *args, **kwargs)

    cls.__init__ = new_init
    return cls


def _log_and_warn(
    message: str,
    warn_type: type[Warning],
    filename: str | None = None,
    line_num: int | None = None,
    function: str | None = None,
) -> None:
    """Log a message and emit a warning using the LocalLogger."""
    from dsbase import LocalLogger

    # Create a context-aware message with location information
    short_name = Path(filename).name if filename else "unknown"
    location = f"{short_name}:{line_num} in {function}" if filename and line_num else ""

    # Create a logger and log the warning
    logger = LocalLogger().get_logger(simple=True)
    log_level = logging.WARNING if warn_type is DeprecationWarning else logging.ERROR
    logger.log(log_level, "%s (%s)", message, location)
