# ruff: noqa: D212, D415

r"""PathKeeper: A friendly cross-platform path management utility.

PathKeeper simplifies working with application and user directories across different operating
systems, providing consistent access to standard locations while respecting platform conventions.

Platform-specific paths:
    Linux:
        data:      ~/.local/share/app_name
        config:    ~/.config/app_name
        cache:     ~/.cache/app_name
        logs:      ~/.cache/app_name/logs
        state:     ~/.local/state/app_name
        documents: ~/Documents

    macOS (adds `app_domain` if provided):
        data:      ~/Library/Application Support/app_domain/app_name
        config:    ~/Library/Preferences/app_name
        cache:     ~/Library/Caches/app_name
        logs:      ~/Library/Logs/app_name
        state:     ~/Library/Application Support/app_domain/app_name
        documents: ~/Documents

    Windows:
        data:      C:\\Users\\<user>\\AppData\\Local\\app_author\\app_name
        config:    C:\\Users\\<user>\\AppData\\Local\\app_author\\app_name\\Config
        cache:     C:\\Users\\<user>\\AppData\\Local\\app_author\\app_name\\Cache
        logs:      C:\\Users\\<user>\\AppData\\Local\\app_author\\app_name\\Logs
        state:     C:\\Users\\<user>\\AppData\\Local\\app_author\\app_name
        documents: C:\\Users\\<user>\\Documents

Examples:
    Basic usage:
        paths = PathKeeper("myapp")
        config_file = paths.from_config("settings.json")
        cache_dir = paths.from_cache("responses")

    With author and domain (recommended for macOS):
        paths = PathKeeper(
            app_name="MyApp",
            app_author="DeveloperName",
            app_domain_prefix="com.developername",
        )
"""

from __future__ import annotations

from .path_keeper import PathKeeper
