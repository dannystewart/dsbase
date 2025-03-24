from __future__ import annotations

import sys

from dsbase.util.traceback import log_traceback


def dsbase_setup() -> None:
    """Configure the system to log tracebacks for unhandled exceptions."""
    sys.excepthook = lambda exctype, value, tb: log_traceback((exctype, value, tb))
