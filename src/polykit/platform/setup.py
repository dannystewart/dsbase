from __future__ import annotations

import sys

from polykit.packages import VersionChecker, VersionInfo


def polykit_setup() -> VersionInfo:
    """Configure the system with standard setup options.

    Sets up exception handling and automatically records version information.

    Returns:
        VersionInfo object with version details. The return isn't needed if you aren't going to use
        it for anything, but it's available in case you need version information for something.
    """
    from polykit.core import log_traceback
    from polykit.env import PolyEnv
    from polykit.log import PolyLog

    # Configure exception handling
    sys.excepthook = lambda exctype, value, tb: log_traceback((exctype, value, tb))

    # Automatically determine package name
    package_name = VersionChecker.get_caller_package_name()

    # Get and log version information
    version_info = VersionChecker.get_version_info(package_name)

    env = PolyEnv()
    env.add_bool("SHOW_VER")
    level = "DEBUG" if env.show_ver else "INFO"

    logger = PolyLog.get_logger(level=level, simple=True)
    logger.debug("Starting %s", version_info)

    return version_info
