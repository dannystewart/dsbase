from __future__ import annotations

import sys

from dsbase.util.traceback import log_traceback
from dsbase.version import VersionChecker, VersionInfo


def dsbase_setup() -> VersionInfo:
    """Configure the system with standard setup options.

    Sets up exception handling and automatically records version information.

    Returns:
        VersionInfo object with version details. The return isn't needed if you aren't going to use
        it for anything, but it's available in case you need version information for something.
    """
    # Configure exception handling
    sys.excepthook = lambda exctype, value, tb: log_traceback((exctype, value, tb))

    # Automatically determine package name
    package_name = VersionChecker.get_caller_package_name()

    # Get and log version information
    version_info = VersionChecker.get_version_info(package_name)

    from dsbase import EnvManager, LocalLogger

    env = EnvManager()
    env.add_bool("SHOW_VER")
    level = "DEBUG" if env.show_ver else "INFO"

    logger = LocalLogger().get_logger(level=level, simple=True)
    logger.debug("Starting %s", version_info)

    return version_info
