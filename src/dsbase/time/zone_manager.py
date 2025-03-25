from __future__ import annotations

import warnings
from zoneinfo import ZoneInfo

from tzlocal import get_localzone

from dsbase.util import Singleton


class TimeZoneManager(metaclass=Singleton):
    """Singleton class for managing the local timezone."""

    _warning_shown = False

    def __init__(self):
        self._timezone = self._detect_timezone()

    def _detect_timezone(self) -> ZoneInfo:
        try:  # Try to get the local timezone
            local_tz_str = str(get_localzone())
            return ZoneInfo(local_tz_str)
        except Exception:
            # If detection fails, show a warning on the first check only
            if not TimeZoneManager._warning_shown:
                warn_text = "Could not detect local timezone, defaulting to America/New_York"
                warnings.warn(warn_text, UserWarning, stacklevel=2)
                TimeZoneManager._warning_shown = True

            return ZoneInfo("America/New_York")

    def get_timezone(self) -> ZoneInfo:
        """Get the local timezone."""
        return self._timezone


# Create TZ object for easy access
TZ = TimeZoneManager().get_timezone()
