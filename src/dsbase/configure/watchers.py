from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING, Any

from dsbase import LocalLogger
from dsbase.util.deprecate import not_yet_implemented
from dsbase.util.singleton import Singleton

if TYPE_CHECKING:
    from collections.abc import Callable
    from logging import Logger

    from watchdog.events import FileSystemEvent


@not_yet_implemented("Configuration system is not yet implemented.")
class ConfigFileHandler:
    """Handler for configuration file system events."""

    def __init__(self, watcher: ConfigWatcher):
        """Initialize the file system event handler with the ConfigWatcher instance that owns it."""
        self.logger: Logger = LocalLogger().get_logger()
        self.watcher = watcher

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if not event.is_directory and str(event.src_path) in self.watcher.watched_files:
            self._notify_callbacks(str(event.src_path), "modified")

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if event.is_directory:
            return

        path_str = str(event.src_path)
        if any(path_str.startswith(str(d)) for d in self.watcher.watched_dirs):
            self._notify_callbacks(path_str, "created")

    def _notify_callbacks(self, path: str, event_type: str) -> None:
        """Notify all registered callbacks for a path.

        Args:
            path: The path that triggered the event.
            event_type: The type of event (modified, created, etc.).
        """
        path_str = str(path)  # Ensure we're working with strings

        # Call callbacks for the specific file
        self._notify_path_callbacks(path_str, event_type)

        # Call callbacks for parent directories
        for dir_path in self.watcher.watched_dirs:
            dir_str = str(dir_path)
            if path_str.startswith(dir_str):
                self._notify_path_callbacks(dir_str, event_type, path_str)

    def _notify_path_callbacks(
        self, registered_path: str, event_type: str, actual_path: str | None = None
    ) -> None:
        """Notify callbacks registered for a specific path.

        Args:
            registered_path: The path callbacks are registered for.
            event_type: The type of event.
            actual_path: The actual path that changed (defaults to the registered path).
        """
        if actual_path is None:
            actual_path = registered_path

        for callback in self.watcher.callbacks.get(registered_path, []):
            try:
                callback(actual_path)
                self.logger.debug("File %s: %s", event_type, actual_path)
            except Exception as e:
                self.logger.error("Error in callback: %s", str(e))


@not_yet_implemented("Configuration system is not yet implemented.")
class ConfigWatcher(metaclass=Singleton):
    """Watches configuration files for changes and triggers reloads."""

    def __init__(self):
        """Initialize the file watcher."""
        self.logger: Logger = LocalLogger().get_logger()
        self.callbacks: dict[str, list[Callable[[str], None]]] = {}
        self.watched_files: set[str] = set()
        self.watched_dirs: set[str] = set()
        self._lock: Lock = Lock()
        self._observer: Any = None
        self._handler: Any = None

    def watch_file(self, path: str | Path, callback: Callable[[str], None]) -> None:
        """Watch a file for changes.

        Args:
            path: The path to the file to watch.
            callback: The function to call when the file changes.
        """
        path_str = str(path)
        with self._lock:
            # Register the callback
            if path_str not in self.callbacks:
                self.callbacks[path_str] = []
            if callback not in self.callbacks[path_str]:
                self.callbacks[path_str].append(callback)

            # Skip if already watching
            if path_str in self.watched_files:
                return

            self.watched_files.add(path_str)

            # Start observer if needed
            self._ensure_observer_running()

            # Add the file to the observer
            if Path(path_str).is_file():
                self._add_watch(path_str)

    def watch_directory(self, directory: str | Path, callback: Callable[[str], None]) -> None:
        """Watch a directory for changes.

        Args:
            directory: The path to the directory to watch.
            callback: The function to call when files in the directory change.
        """
        dir_str = str(directory)
        with self._lock:
            # Register the callback
            if dir_str not in self.callbacks:
                self.callbacks[dir_str] = []
            if callback not in self.callbacks[dir_str]:
                self.callbacks[dir_str].append(callback)

            # Skip if already watching
            if dir_str in self.watched_dirs:
                return

            self.watched_dirs.add(dir_str)

            # Start observer if needed
            self._ensure_observer_running()

            # Add the directory to the observer
            if Path(dir_str).is_dir():
                self._add_watch(dir_str, recursive=True)

    def _ensure_observer_running(self) -> None:
        """Ensure the file observer is running."""
        if self._observer is None:
            # Import here to avoid circular imports
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer

            # Create a handler adapter class that extends FileSystemEventHandler
            class HandlerAdapter(FileSystemEventHandler):
                def __init__(self, handler: ConfigFileHandler):
                    self.handler = handler

                def on_modified(self, event: FileSystemEvent) -> None:
                    self.handler.on_modified(event)

                def on_created(self, event: FileSystemEvent) -> None:
                    self.handler.on_created(event)

            # Create our handler and adapter
            handler = ConfigFileHandler(self)
            adapter = HandlerAdapter(handler)

            # Start the observer
            self._observer = Observer()
            self._handler = adapter
            self._observer.start()

    def _add_watch(self, path: str, recursive: bool = False) -> None:
        """Add a path to the watchdog observer.

        Args:
            path: The path to watch.
            recursive: Whether to watch the directory recursively.
        """
        directory = path if Path(path).is_dir() else str(Path(path).parent)
        self._observer.schedule(self._handler, directory, recursive=recursive)

    def stop(self) -> None:
        """Stop watching for file changes."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
