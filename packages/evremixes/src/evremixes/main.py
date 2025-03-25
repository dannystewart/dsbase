from __future__ import annotations

from dsbase.env import EnvManager
from dsbase.util import dsbase_setup

from evremixes.config import DownloadConfig
from evremixes.metadata_helper import MetadataHelper
from evremixes.track_downloader import TrackDownloader

dsbase_setup()


class EvRemixes:
    """Evanescence Remix Downloader."""

    def __init__(self) -> None:
        self.env = EnvManager()
        self.env.add_bool("EVREMIXES_ADMIN", attr_name="admin", required=False)

        # Initialize configuration and helpers
        self.config = DownloadConfig.create(is_admin=self.env.admin)
        self.metadata_helper = MetadataHelper(self.config)
        self.download_helper = TrackDownloader(self.config)

        # Get track metadata
        self.album_info = self.metadata_helper.get_metadata()

    def download_tracks(self) -> None:
        """Download the tracks."""
        if self.config.is_admin:
            self.download_helper.download_tracks_for_admin(self.album_info)
        else:
            self.download_helper.download_tracks(self.album_info, self.config)


def main() -> None:
    """Run the Evanescence Remix Downloader."""
    evremixes = EvRemixes()
    evremixes.download_tracks()
