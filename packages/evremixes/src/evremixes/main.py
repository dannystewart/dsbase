"""The official versions of my remixes are the ones published on my website at
https://music.dannystewart.com/evanescence. This script grabs them from there, using the
evtracks.json file holding the current list of available remixes, metadata, and URLs.

You're presented with the choice of FLAC or ALAC (Apple Lossless), as well as where you want the
files to be saved. The default options are your Downloads and Music folders, but you can also enter
a custom path. After downloading, it will apply the correct metadata, album art, and filenames.
"""

from __future__ import annotations

from dsbase.env import EnvManager
from dsbase.util import dsbase_setup
from dsbase.util.argparser import ArgParser

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
    # Set up argument parser for `--version`
    parser = ArgParser(description=__doc__)
    parser.parse_args()

    # Initialize the downloader
    evremixes = EvRemixes()
    evremixes.download_tracks()
