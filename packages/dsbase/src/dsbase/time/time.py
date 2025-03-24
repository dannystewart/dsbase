from __future__ import annotations

from datetime import datetime, timedelta
from functools import partial
from typing import Any, ClassVar
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")


class Time:
    """Time parser and formatter for various formats and relative time interpretations."""

    # Days of the week, for converting name to number
    DAYS: ClassVar[list[str]] = [
        "Monday",  # 0
        "Tuesday",  # 1
        "Wednesday",  # 2
        "Thursday",  # 3
        "Friday",  # 4
        "Saturday",  # 5
        "Sunday",  # 6
    ]

    @staticmethod
    def parse(time_str: str, ref_time: datetime | None = None) -> datetime | None:
        """Parse a time string into a timezone-aware datetime, relative to the reference time.

        Handles various formats including:
            - 12-hour time (2:30 pm, 2pm, 2:30)
            - 24-hour time (14:30, 1430)
            - Natural language (now, today, tomorrow)

        Args:
            time_str: The time string to parse.
            ref_time: An optional reference time to use (defaults to current time).

        Returns:
            Parsed datetime object or None if parsing fails.
        """
        now = ref_time or datetime.now(TZ)
        normalized = time_str.lower().replace("am", " am").replace("pm", " pm").strip()

        # Handle special cases and try custom parser first
        if normalized == "now":
            return now
        if parsed := Time._parse_simple(normalized, now):
            return parsed

        try:  # Fall back to dateutil parser if available
            from dateutil import parser

            parsed = parser.parse(time_str, fuzzy=True, default=now)
            return Time.ensure_future(
                Time.ensure_tz(parsed), now, force_future="today" not in normalized
            )
        except (ValueError, ImportError):
            return None

    @staticmethod
    def _parse_12_hour(now: datetime, time_str: str) -> datetime | None:
        parts = time_str.split()
        time_parts = parts[0].split(":")

        if len(time_parts) in {1, 2} and time_parts[0].isdigit():
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) == 2 else 0

            if 1 <= hour <= 12 and 0 <= minute < 60:  # If AM/PM is explicitly specified
                if len(parts) == 2:
                    if parts[1] == "pm" and hour != 12:
                        hour += 12
                    elif parts[1] == "am" and hour == 12:
                        hour = 0
                else:  # If no AM/PM specified, interpret as the next upcoming time
                    current_hour = now.hour
                    if current_hour < 12:  # It's currently AM
                        if hour < current_hour or (hour == current_hour and minute <= now.minute):
                            # Time has passed for today, assume PM
                            hour += 12
                    elif hour < 12:
                        if hour > current_hour - 12 or (
                            hour == current_hour - 12 and minute > now.minute
                        ):  # Time is still upcoming today
                            hour += 12
                return Time.adjust_for_tomorrow_if_needed(now, hour, minute)

        return None

    @staticmethod
    def _parse_24_hour(now: datetime, time_str: str) -> datetime | None:
        if ":" in time_str:  # Try to parse with colon
            parts = time_str.split(":")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                hour = int(parts[0])
                minute = int(parts[1])
                if 0 <= hour < 24 and 0 <= minute < 60:
                    return Time.adjust_for_tomorrow_if_needed(now, hour, minute)

        if time_str.isdigit() and len(time_str) == 4:  # Otherwise, try without colon
            hour = int(time_str[:2])
            minute = int(time_str[2:])
            if 0 <= hour < 24 and 0 <= minute < 60:
                return Time.adjust_for_tomorrow_if_needed(now, hour, minute)

        return None

    @staticmethod
    def adjust_for_tomorrow_if_needed(
        time: datetime | None = None, hour: int | None = None, minute: int | None = None
    ) -> datetime:
        """Adjust the given time to the next occurrence within 24 hours.

        If hour and minute are provided, it sets the time to those values before adjusting. If no
        arguments are provided, it uses the current time.
        """
        # Get the current time
        now = datetime.now(TZ)

        # Set the time to the specified hour and minute if provided
        if hour is not None and minute is not None:
            time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Use the current time if no time was provided, and ensure timezone
        time = time or now
        time = Time.ensure_tz(time)

        if time <= now:  # If the time is in the past, move it to tomorrow
            time += timedelta(days=1)

        return time

    @staticmethod
    def get_pretty_time(time: datetime | timedelta, **kwargs: Any) -> str:
        """Given a timestamp, return a pretty string representation of the time.

        Args:
            time: The timestamp to convert.
            **kwargs: Additional keyword arguments to pass to the formatting function.
                - capitalize: If True, the first letter of the string will be capitalized.
                - time_only: If True, only the time will be returned, not the date.
                - weekday: If True, the weekday will be included in the date format.
                - compact: If True, use a more compact format for dates within 7 days.
        """
        if isinstance(time, datetime):
            return Time._format_datetime(time, **kwargs)
        return Time._format_timedelta(time)

    @staticmethod
    def _parse_simple(time_str: str, ref_time: datetime) -> datetime | None:
        """Parse common time formats using simple string manipulation."""
        if time := Time._parse_12_hour(ref_time, time_str):
            return time
        if time := Time._parse_24_hour(ref_time, time_str):
            return time
        return None

    @staticmethod
    def _format_datetime(
        time: datetime,
        capitalize: bool = False,
        time_only: bool = False,
        weekday: bool = False,
        compact: bool = False,
    ) -> str:
        now = datetime.now(tz=TZ)

        if time_only:
            return time.strftime("%-I:%M %p")

        days_difference = (time.date() - now.date()).days

        if days_difference == 0:
            result = f"today at {time.strftime('%-I:%M %p')}"
        elif days_difference == -1:
            result = f"yesterday at {time.strftime('%-I:%M %p')}"
        elif days_difference == 1:
            result = f"tomorrow at {time.strftime('%-I:%M %p')}"
        elif compact and 1 < abs(days_difference) <= 7:
            result = time.strftime("%A at %-I:%M %p")
        else:
            result = time.strftime("%A, %B %d") if weekday or compact else time.strftime("%B %d")
            if abs(days_difference) > 365:
                result += time.strftime(", %Y")
            result += f" at {time.strftime('%-I:%M %p')}"

        return result.capitalize() if capitalize else result

    @staticmethod
    def _format_timedelta(time: timedelta) -> str:
        total_seconds = int(time.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours}h {minutes}m {seconds}s"

    @staticmethod
    def convert_to_12h(hour: int, minutes: int = 0) -> str:
        """Convert 24-hour time to 12-hour time format with AM/PM, including minutes.

        Args:
            hour: The hour in 24-hour format.
            minutes: The minutes.
        """
        period = "PM" if hour >= 12 else "AM"
        if hour > 12:
            hour -= 12
        elif hour == 0:
            hour = 12

        # Ensure minutes are always two digits
        minutes_formatted = f"{minutes:02d}"

        return f"{hour}:{minutes_formatted} {period}"

    @staticmethod
    def convert_min_to_interval(interval: int) -> str:
        """Convert a time interval in minutes to a human-readable interval string."""
        hours, minutes = divmod(interval, 60)

        parts = []
        if hours:
            parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if minutes or not parts:
            parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")

        return " and ".join(parts)

    @staticmethod
    def convert_sec_to_interval(interval: int, omit_one: bool = False) -> str:
        """Convert a time interval in seconds to a human-readable interval string.

        Args:
            interval: The time interval in seconds.
            omit_one: If True, the string will not include the unit if the value is 1.

        Returns:
            A human-readable string representation of the time interval.
        """
        days, remainder = divmod(interval, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if days:
            parts.append(f"{days} day{'s' if days > 1 else ''}")
        if hours:
            parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if minutes:
            parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
        if seconds or not parts:
            parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")

        if omit_one:
            parts = [p.replace("1 ", "") if p.startswith("1 ") else p for p in parts]

        return " and ".join(parts)

    @staticmethod
    def add_time_to_datetime(
        original_datetime: datetime,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
    ) -> datetime:
        """Add hours, minutes, and seconds to a datetime object.

        Args:
            original_datetime: The original datetime object to be adjusted.
            hours: The number of hours to add. Defaults to 0.
            minutes: The number of minutes to add. Defaults to 0.
            seconds: The number of seconds to add. Defaults to 0.
        """
        return original_datetime + timedelta(hours=hours, minutes=minutes, seconds=seconds)

    @staticmethod
    def ensure_tz(dt: datetime) -> datetime:
        """Ensure datetime has the correct timezone."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=TZ)
        return dt.astimezone(TZ)

    @staticmethod
    def ensure_future(dt: datetime, ref_time: datetime, force_future: bool = True) -> datetime:
        """Ensure the datetime is in the future relative to the reference time."""
        if dt <= ref_time and force_future:
            return dt + timedelta(days=1)
        return dt

    @staticmethod
    def get_day_number(day: str) -> int:
        """Convert day name to day number (0-6, where Monday is 0)."""
        return Time.DAYS.index(day)


# Partial functions for common use cases
get_pretty_time = partial(Time.get_pretty_time)
get_capitalized_time = partial(Time.get_pretty_time, capitalize=True)
get_time_only = partial(Time.get_pretty_time, time_only=True)
get_weekday_time = partial(Time.get_pretty_time, weekday=True)
