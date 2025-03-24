from __future__ import annotations


def is_doc_tool() -> bool:
    """Check if code is being imported for documentation generation."""
    import sys

    return any("pdoc" in arg for arg in sys.argv) or "sphinx" in sys.modules


def platform_check(platform_name: str = "Darwin", exit_on_mismatch: bool = True) -> bool:
    """Check if running on the specified platform.

    Args:
        platform_name: The platform name to check for (default: "Darwin" for macOS).
        exit_on_mismatch: Whether to exit if not on the specified platform.

    Returns:
        bool: True if on the specified platform, False otherwise.

    Note:
        When being imported for documentation, this function will always return True and will not
        exit, regardless of the actual platform.
    """
    import os
    import sys

    from dsbase.text import print_colored

    # Skip actual check if being imported for documentation
    if is_doc_tool():
        return True

    is_correct_platform = os.uname().sysname == platform_name

    if not is_correct_platform and exit_on_mismatch:
        message = f"This can only be run on {platform_name}. Aborting."
        print_colored(message, "red")

        # Only exit if running as a script, not when imported
        if __name__ == "__main__":
            sys.exit(1)

    return is_correct_platform
