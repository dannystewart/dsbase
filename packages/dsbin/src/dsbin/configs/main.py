"""This script will download config files for various coding tools which are then used as reference
to compare against files with the same name in the directory where the script is run. This is to
ensure that I always have the latest versions of my preferred configurations for all my projects.

Note that these config files live in the dsbin repository: https://github.com/dannystewart/dsbase

The script also saves the updated config files to the package root, which is the root of the dsbin
repository itself, thereby creating a virtuous cycle where the repo is always up-to-date with the
latest versions of the config files for other projects to pull from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import requests

from dsbase import ArgParser, FileManager, LocalLogger
from dsbase.shell import confirm_action
from dsbase.text.diff import show_diff

if TYPE_CHECKING:
    import argparse

logger = LocalLogger().get_logger()
files = FileManager()


@dataclass
class ConfigFile:
    """Represents a config file that can be updated from a remote source."""

    # Base URL for the repository
    CONFIG_ROOT: ClassVar[str] = "https://raw.githubusercontent.com/dannystewart/dsbin/main/configs"

    name: str
    url: str = field(init=False)
    local_path: Path = field(init=False)

    def __post_init__(self):
        self.url = f"{self.CONFIG_ROOT}/{self.name}"
        self.local_path = Path.cwd() / self.name


# Define the configs to manage
CONFIGS = [
    ConfigFile("ruff.toml"),
    ConfigFile("mypy.ini"),
]


def update_configs(skip_confirm: bool = False) -> None:
    """Pull down latest configs from repository, updating local copies."""
    changes_made = set()
    should_create_all = not any(config.local_path.exists() for config in CONFIGS)

    if should_create_all:
        logger.debug("No existing configs found; downloading and creating all available configs.")

    for config in CONFIGS:
        # Get content from remote
        remote_content = fetch_remote_content(config)
        if not remote_content:
            logger.error("Failed to update %s config - not available remotely.", config.name)
            continue

        # Process the config
        if process_config(config, remote_content, skip_confirm, should_create_all):
            changes_made.add(config.name)

    # Report unchanged configs
    unchanged = [c.name for c in CONFIGS if c.name not in changes_made]
    if unchanged:
        logger.info("No changes needed for: %s", ", ".join(unchanged))


def fetch_remote_content(config: ConfigFile) -> str | None:
    """Fetch content from remote URL."""
    try:
        response = requests.get(config.url)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        logger.warning("Failed to download %s from remote.", config.name)
        return None


def process_config(
    config: ConfigFile,
    remote_content: str,
    skip_confirm: bool,
    should_create_all: bool,
) -> bool:
    """Process a single config file, updating or creating as needed.

    Returns:
        True if the config was updated or created, False otherwise.
    """
    if config.local_path.exists():
        local_content = config.local_path.read_text()
        if local_content == remote_content:
            return False

        if not skip_confirm:
            show_diff(local_content, remote_content, config.local_path.name)
            if not confirm_action(f"Update {config.name} config?", default_to_yes=True):
                return False
    elif not (
        skip_confirm
        or should_create_all
        or confirm_action(
            f"{config.name} config does not exist locally. Create?",
            default_to_yes=True,
        )
    ):
        return False

    config.local_path.write_text(remote_content)
    action = "Created" if not config.local_path.exists() else "Updated"
    logger.info("%s %s config from remote.", action, config.name)
    return True


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = ArgParser(description="Update config files from central repository")
    parser.add_argument("-y", action="store_true", help="update files without confirmation")
    return parser.parse_args()


def main() -> None:
    """Fetch and update the config files."""
    args = parse_args()
    update_configs(skip_confirm=args.y)


if __name__ == "__main__":
    main()
