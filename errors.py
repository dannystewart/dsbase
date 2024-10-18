from __future__ import annotations

import functools
import inspect
import logging
import sys
import traceback
import types
from typing import Any, Callable

try:
    from pygments import highlight
    from pygments.formatters import TerminalFormatter
    from pygments.lexers import PythonTracebackLexer

    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False


def log_traceback(exc_info: tuple | None = None, trim_levels: int = 0) -> None:
    """Log a traceback, optionally trimming unwanted levels."""
    # Unpack traceback info
    exc_type, exc_value, exc_traceback = exc_info or sys.exc_info()

    # Trim traceback to set number of levels
    for _ in range(trim_levels):
        if exc_traceback is not None:
            exc_traceback = exc_traceback.tb_next

    # Log traceback and exception details
    if exc_value is not None and exc_traceback is not None:
        tb_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb = "".join(tb_list)
        if PYGMENTS_AVAILABLE:
            tb = highlight(tb, PythonTracebackLexer(), TerminalFormatter())
        else:
            print("Can't colorize traceback because Pygments is not installed.")
        sys.stderr.write(tb)


def configure_traceback() -> None:
    """Configure the system to log tracebacks for unhandled exceptions."""
    sys.excepthook = lambda exctype, value, tb: log_traceback((exctype, value, tb))


def catch_errors(
    show_tb: bool = True,
    on_error: Callable | None = None,
    default_return: Any | None = None,
    trim_levels: int = 1,
) -> Callable:
    """
    Enhance functions with advanced error handling and logging.

    Args:
        show_tb: When True, additional info will be logged, including stack traces. Helpful in
            instances where more detail is needed. Defaults to True.
        on_error: A callback function that's invoked when an exception is caught. The function
            receives the exception as an argument. Useful for additional handling or logging beyond
            what's provided by the decorator. Defaults to None.
        default_return: The value to return from the decorated function when an exception is caught
            and handled. Ensures a consistent interface even in error conditions. Defaults to None.
        trim_levels: The number of levels to trim when identifying the calling function. Useful for
            removing wrapper functions from the traceback. Defaults to 1.
    """

    def error_decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def error_catcher(*args: Any, **kwargs: Any) -> Any:
            logger = get_logger_for_caller(func, *args)

            try:
                return func(*args, **kwargs)

            except Exception as e:
                if getattr(e, "_logged", False):
                    raise  # Raise if not already logged

                formatted_e = get_formatted_error(func, e, trim_levels)
                logger.error(formatted_e)

                if show_tb:
                    log_traceback(trim_levels=trim_levels)

                setattr(e, "_logged", True)  # Mark it as logged

                if on_error:
                    on_error(e)  # Call the on_error callback if one was provided

                return default_return

        return error_catcher

    return error_decorator


def get_logger_for_caller(func: Callable, *args: Any) -> logging.Logger:
    """Get the logger from the instance or module, or use the default logger."""
    instance = args[0] if args and not isinstance(args[0], types.ModuleType) else None
    return getattr(instance, "logger", None) or logging.getLogger(func.__module__)


def get_caller_name(start_index: int = 1) -> str | None:
    """
    Traverses the stack to find the name of the caller function along with its class.

    Args:
        start_index: The index in the stack to start from.

    Returns:
        The name of the caller function with class (if any), or None if not found.
    """
    stack = inspect.stack()

    # Traverse the stack to find the caller function's name based on specified skips
    for frame_info in stack[start_index:]:
        class_name = None
        if "self" in frame_info.frame.f_locals:  # Check if this is a method in a class
            class_name = frame_info.frame.f_locals["self"].__class__.__name__
        function_name = frame_info.function
        return f"{class_name}.{function_name}" if class_name else function_name
    return None  # If no suitable function is found, return None


def get_formatted_error(func: Callable, e: Exception, trim_levels: int = 0) -> str:
    """Format error message with caller name and exception type."""
    error_msg = "{exception_type} in '{func_name}': {error} (called by '{caller}')"

    query_details = ""
    if hasattr(e, "query"):
        query_details = f"\nQuery: {e.query}"  # type: ignore
        if hasattr(e, "params"):
            params_message = ", ".join(repr(p) for p in e.params)  # type: ignore
            query_details += f"\nParams: {params_message}"

    return error_msg.format(
        exception_type=type(e).__name__,
        func_name=func.__name__,
        caller=get_caller_name(start_index=2 + trim_levels),
        error=str(e) + query_details,
    )
