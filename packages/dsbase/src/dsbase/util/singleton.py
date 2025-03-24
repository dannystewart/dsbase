from __future__ import annotations

from threading import Lock
from typing import Any, ClassVar, TypeVar

T = TypeVar("T")


class Singleton(type):
    """Thread-safe metaclass for creating singleton classes.

    A metaclass that ensures classes have only one instance throughout the program's lifetime.
    Implements thread-safe instance creation using class-level locks, preventing race conditions
    during instantiation. Instance tracking is handled through private class variables.

    This implementation uses a class-level dictionary to track instances by class and maintains
    separate locks for each class to ensure thread safety. The first instantiation creates and
    stores the instance, and subsequent instantiations return the stored instance.

    # Basic usage is as simple as this:

        class MyService(metaclass=Singleton):
            def __init__(self):
                pass

    # If additional class-specific initialization is needed:

            def __init__(self):
                self._initialized = False

            def initialize(self) -> None:
                if not self._initialized:
                    self.do_thing()
                    self._initialized = True
    """

    __instances: ClassVar[dict[type, Any]] = {}
    __locks: ClassVar[dict[type, Lock]] = {}

    def __call__(cls: type[T], *args: Any, **kwargs: Any) -> T:
        """Create a new instance of the class if one does not already exist."""
        if cls not in Singleton.__locks:
            Singleton.__locks[cls] = Lock()

        with Singleton.__locks[cls]:
            if cls not in Singleton.__instances:
                instance = super().__call__(*args, **kwargs)
                Singleton.__instances[cls] = instance
            return Singleton.__instances[cls]
