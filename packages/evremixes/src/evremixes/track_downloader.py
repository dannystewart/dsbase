from __future__ import annotations

import contextlib
import os
import platform
import string
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import requests
from halo import Halo
from termcolor import colored

from dsbase.log import LocalLogger
from dsbase.text import print_colored
from dsbase.util import handle_interrupt

from evremixes.metadata_helper import MetadataHelper
from evremixes.types import AudioFormat, TrackVersions

if TYPE_CHECKING:
    from logging import Logger

    from evremixes.config import DownloadConfig
    from evremixes.types import AlbumInfo


class TrackDownloader:
    """Helper class for downloading tracks."""

    def __init__(self, config: DownloadConfig) -> None:
        self.config = config
        self.metadata = MetadataHelper(config)
        self.logger: Logger = LocalLogger().get_logger()

    @handle_interrupt()
    def download_tracks(self, album_info: AlbumInfo, config: DownloadConfig) -> None:
        """Download tracks according to configuration.

        Raises:
            ValueError: If the configuration is incomplete.
        """
        if config.versions is None or config.audio_format is None or config.location is None:
            msg = "Download configuration is incomplete"
            raise ValueError(msg)

        # Sanitize album name for folder creation
        valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
        album_name = "".join(c for c in album_info.album_name if c in valid_chars)

        # Get base output folder
        base_folder = config.location / album_name

        match config.versions:
            case TrackVersions.ORIGINAL:
                self._download_track_set(
                    album_info, base_folder, config.audio_format, is_instrumental=False
                )
            case TrackVersions.INSTRUMENTAL:
                self._download_track_set(
                    album_info, base_folder, config.audio_format, is_instrumental=True
                )
            case TrackVersions.BOTH:
                self._download_track_set(
                    album_info, base_folder, config.audio_format, is_instrumental=False
                )
                print()
                self._download_track_set(
                    album_info,
                    base_folder / "Instrumentals",
                    config.audio_format,
                    is_instrumental=True,
                )

        if not config.is_admin:
            print_colored("\nEnjoy!", "green")

        self.open_folder_in_os(base_folder)

    @handle_interrupt()
    def _download_track_set(
        self,
        album_info: AlbumInfo,
        output_folder: Path,
        file_format: AudioFormat,
        is_instrumental: bool,
    ) -> None:
        """Download a single complete set of tracks."""
        output_folder.mkdir(parents=True, exist_ok=True)
        self.remove_previous_downloads(output_folder)

        display_folder = self.format_path_for_display(output_folder)
        print_colored(f"Downloading in {file_format.display_name} to {display_folder}...\n", "cyan")

        # Choose cover art based on track type
        cover_url = album_info.inst_art_url if is_instrumental else album_info.cover_art_url
        cover_data = self.metadata.get_cover_art(cover_url)

        spinner = Halo(spinner="dots")
        total_tracks = len(album_info.tracks)

        for index, track in enumerate(album_info.tracks, start=1):
            track_number = f"{track.track_number:02d}"
            track_name = track.track_name

            if is_instrumental:
                file_url = track.inst_url.rsplit(".", 1)[0] + f".{file_format.extension}"
                if not track_name.endswith(" (Instrumental)"):
                    track_name += " (Instrumental)"
            else:
                file_url = track.file_url.rsplit(".", 1)[0] + f".{file_format.extension}"

            output_path = output_folder / f"{track_number} - {track_name}.{file_format.extension}"

            spinner.text = colored(f"Downloading {track_name}... ({index}/{total_tracks})", "cyan")
            spinner.start()

            try:
                response = requests.get(file_url, stream=True, timeout=30)
                response.raise_for_status()
                output_path.write_bytes(response.content)

                spinner.text = colored("Applying metadata...", "cyan")
                success = self.metadata.apply_metadata(
                    track, album_info, output_path, cover_data, is_instrumental
                )

                if not success:
                    spinner.fail(colored(f"Failed to add metadata to {track_name}.", "red"))
                    continue

                spinner.succeed(colored(f"Downloaded {track_name}", "green"))

            except requests.RequestException:
                spinner.fail(colored(f"Failed to download {track_name}.", "red"))

        spinner.stop()

        end_message = (
            f"All {total_tracks} {'instrumentals' if is_instrumental else 'remixes'} "
            f"downloaded in {file_format.display_name} to {display_folder}."
        )
        print_colored(f"\n{end_message}", "green")

    @handle_interrupt()
    def download_tracks_for_admin(self, album_info: AlbumInfo) -> None:
        """Download all track versions to the custom OneDrive location."""
        base_path = self.config.onedrive_folder

        # Download all combinations
        for file_format in AudioFormat:
            # Original tracks
            output_folder = base_path / Path(file_format.display_name)
            self._download_track_set(album_info, output_folder, file_format, is_instrumental=False)
            print()
            # Instrumental tracks
            output_folder = base_path / Path(f"Instrumentals {file_format.display_name}")
            self._download_track_set(album_info, output_folder, file_format, is_instrumental=True)
            print()

        self.open_folder_in_os(base_path)

    def remove_previous_downloads(self, output_folder: str | Path) -> None:
        """Remove any existing files with the specified file extension in the output folder."""
        output_folder = Path(output_folder)
        file_extensions = (".flac", ".m4a")

        # Remove matching files
        for file_path in output_folder.rglob("*"):
            if file_path.suffix.lower() in file_extensions:
                try:
                    file_path.unlink()
                except Exception as e:
                    self.logger.error("Failed to delete %s: %s", file_path, str(e))

        # Remove empty directories from bottom up
        for dirpath in sorted(
            output_folder.rglob("*"), key=lambda x: len(str(x.resolve()).split("/")), reverse=True
        ):
            if dirpath.is_dir():
                with contextlib.suppress(OSError):
                    dirpath.rmdir()

    def open_folder_in_os(self, output_folder: str | Path) -> None:
        """Open the output folder in the OS file browser."""
        with contextlib.suppress(Exception):
            output_folder = Path(output_folder).resolve()
            os_type = platform.system()

            if os_type == "Windows":
                subprocess.run(["explorer", str(output_folder)], check=False)
            elif os_type == "Darwin":
                subprocess.run(["open", str(output_folder)], check=False)
            elif os_type == "Linux" and "DISPLAY" in os.environ:
                subprocess.run(["xdg-open", str(output_folder)], check=False)

    def format_path_for_display(self, path: Path) -> str:
        """Convert a path to a user-friendly display format with ~ for home directory."""
        path_delimiter = "/" if platform.system() != "Windows" else "\\"
        try:
            return f"~{path_delimiter}{path.relative_to(Path.home())}"
        except ValueError:
            return str(path)
