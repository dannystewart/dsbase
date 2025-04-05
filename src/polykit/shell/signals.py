from __future__ import annotations

import sys
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from logging import Logger

T = TypeVar("T")


def handle_interrupt(
    message: str = "Interrupted by user. Exiting...",
    exit_code: int = 1,
    callback: Callable[..., Any] | None = None,
    use_newline: bool = False,
    logger: Logger | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Handle KeyboardInterrupt exceptions.

    Args:
        message: The message to display when interrupted.
        exit_code: The exit code to use when terminating.
        callback: An optional function to call before exiting.
        use_newline: Whether to print a newline before the message.
        logger: An optional logger to use rather than creating a new one.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except KeyboardInterrupt:
                if use_newline:  # Move to next line without clearing current line
                    sys.stdout.write("\n")
                else:  # Clear the current line
                    sys.stdout.write("\r\033[K")
                sys.stdout.flush()

                if callback:  # Check the signature of the callback function
                    import inspect
                    import signal

                    sig = inspect.signature(callback)
                    param_count = len([
                        p
                        for p in sig.parameters.values()
                        if p.default == inspect.Parameter.empty
                        and p.kind
                        not in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}
                    ])

                    # Call the callback with appropriate arguments
                    if param_count == 0:
                        callback()
                    elif "signum" in sig.parameters and "frame" in sig.parameters:
                        callback(signal.SIGINT, None)  # Signal handler style callback
                    else:
                        callback(*args, **kwargs)  # Pass the original arguments

                if logger:  # Use supplied logger
                    logger.error(message)
                else:  # Create new logger
                    from polykit.log import PolyLog

                    PolyLog.get_logger(simple=True).error(message)
                sys.exit(exit_code)

        return wrapper

    return decorator


def async_interrupt_handler[T](
    func: Callable[..., Awaitable[T]],
    message: str,
    exit_code: int,
    callback: Callable[..., Any] | None,
    use_newline: bool,
    logger: Logger | None,
) -> Callable[..., Awaitable[T]]:
    """Core logic for async interrupt handling."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)
        except KeyboardInterrupt:
            if use_newline:
                sys.stdout.write("\n")
            else:
                sys.stdout.write("\r\033[K")
            sys.stdout.flush()

            if callback:
                import asyncio

                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)

            if logger:  # Use supplied logger
                logger.error(message)
            else:  # Create new logger
                from polykit.log import PolyLog

                PolyLog.get_logger(simple=True).error(message)
            sys.exit(exit_code)

    return wrapper


def async_handle_interrupt(
    message: str = "Interrupted by user. Exiting...",
    exit_code: int = 1,
    callback: Callable[..., Any] | None = None,
    use_newline: bool = False,
    logger: Logger | None = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator to handle KeyboardInterrupt exceptions in async functions."""

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        return async_interrupt_handler(func, message, exit_code, callback, use_newline, logger)

    return decorator


def async_with_handle_interrupt[T](
    func: Callable[..., Awaitable[T]],
    *args: Any,
    message: str = "Interrupted by user. Exiting...",
    exit_code: int = 1,
    callback: Callable[..., Any] | None = None,
    use_newline: bool = False,
    logger: Logger | None = None,
    **kwargs: Any,
) -> T:
    """Run an async function with interrupt handling."""
    import asyncio

    decorated = async_interrupt_handler(func, message, exit_code, callback, use_newline, logger)
    return asyncio.run(decorated(*args, **kwargs))  # type: ignore
