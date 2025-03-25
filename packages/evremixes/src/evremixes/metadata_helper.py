from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

import requests
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover
from PIL import Image

from evremixes.types import AlbumInfo, TrackMetadata

if TYPE_CHECKING:
    from pathlib import Path

    from evremixes.config import DownloadConfig


class MetadataHelper:
    """Helper class for applying metadata to downloaded tracks."""

    def __init__(self, config: DownloadConfig) -> None:
        self.config = config

    def get_metadata(self) -> AlbumInfo:
        """Download the JSON file with all track and album details.

        Raises:
            SystemExit: If the download fails.
        """
        try:
            response = requests.get(self.config.TRACKLIST_URL, timeout=10)
        except requests.RequestException as e:
            raise SystemExit(e) from e

        track_data = json.loads(response.content)
        track_data["tracks"] = sorted(
            track_data["tracks"], key=lambda track: track.get("track_number", 0)
        )
        return AlbumInfo(
            album_name=track_data["metadata"]["album_name"],
            album_artist=track_data["metadata"]["album_artist"],
            artist_name=track_data["metadata"]["artist_name"],
            genre=track_data["metadata"]["genre"],
            year=track_data["metadata"]["year"],
            cover_art_url=track_data["metadata"]["cover_art_url"],
            inst_art_url=track_data["metadata"]["inst_art_url"],
            tracks=[TrackMetadata(**track) for track in track_data["tracks"]],
        )

    def get_cover_art(self, cover_url: str) -> bytes:
        """Download and process the album cover art.

        Raises:
            ValueError: If the download or processing fails.
        """
        try:  # Download the cover art from the URL in the metadata
            cover_response = requests.get(cover_url, timeout=10)
            cover_response.raise_for_status()

            # Resize and convert the cover art to JPEG
            image = Image.open(BytesIO(cover_response.content))
            image = image.convert("RGB")
            image = image.resize((800, 800))

            # Save the resized image as a JPEG and return the bytes
            buffered = BytesIO()
            image.save(buffered, format="JPEG", quality=95, optimize=True)
            return buffered.getvalue()

        except requests.RequestException as e:
            msg = f"Failed to download cover art: {e}"
            raise ValueError(msg) from e
        except OSError as e:
            msg = f"Failed to process cover art: {e}"
            raise ValueError(msg) from e

    def apply_metadata(
        self,
        track: TrackMetadata,
        album_info: AlbumInfo,
        output_path: Path,
        cover_data: bytes,
        is_instrumental: bool,
    ) -> bool:
        """Add metadata and cover art to the downloaded track file. Returns success status.

        Args:
            track: The metadata for the track.
            album_info: The metadata for the album.
            output_path: The path of the downloaded track file.
            cover_data: The cover art, resized and encoded as JPEG.
            is_instrumental: Whether the track is an instrumental.
        """
        try:
            audio_format = output_path.suffix[1:].lower()
            disc_number = 2 if is_instrumental else 1

            # Create display title with instrumental suffix if needed
            display_title = track.track_name
            if is_instrumental and not display_title.endswith(" (Instrumental)"):
                display_title += " (Instrumental)"

            # Apply metadata based on the audio format
            if audio_format == "m4a":
                self._apply_alac_metadata(
                    album_info,
                    output_path,
                    cover_data,
                    track.track_number,
                    disc_number,
                    display_title,
                )
            elif audio_format == "flac":
                self._apply_flac_metadata(
                    album_info,
                    output_path,
                    cover_data,
                    track.track_number,
                    disc_number,
                    display_title,
                )
            return True
        except Exception:
            return False

    def _apply_alac_metadata(
        self,
        album_info: AlbumInfo,
        output_path: Path,
        cover_data: bytes,
        track_number: int,
        disc_number: int,
        display_title: str,
    ) -> None:
        """Apply metadata for ALAC files."""
        audio = MP4(output_path)

        # Add the metadata to the track
        audio["trkn"] = [(track_number, 0)]
        audio["disk"] = [(disc_number, 0)]
        audio["\xa9nam"] = display_title
        audio["\xa9ART"] = album_info.artist_name
        audio["\xa9alb"] = album_info.album_name
        audio["\xa9day"] = str(album_info.year)
        audio["\xa9gen"] = album_info.genre

        # Add the album artist if available
        if album_info.album_artist:
            audio["aART"] = album_info.album_artist

        # Add the cover art to the track
        audio["covr"] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]

        audio.save()

    def _apply_flac_metadata(
        self,
        album_info: AlbumInfo,
        output_path: Path,
        cover_data: bytes,
        track_number: int,
        disc_number: int,
        display_title: str,
    ) -> None:
        """Apply metadata for FLAC files."""
        audio = FLAC(output_path)

        # Add the metadata to the track
        audio["tracknumber"] = str(track_number)
        audio["discnumber"] = str(disc_number)
        audio["title"] = display_title
        audio["artist"] = album_info.artist_name
        audio["album"] = album_info.album_name
        audio["date"] = str(album_info.year)
        audio["genre"] = album_info.genre

        # Add the cover art to the track
        if album_info.album_artist:
            audio["albumartist"] = album_info.album_artist

        # Add the cover art to the track
        pic = Picture()
        pic.data = cover_data
        pic.type = 3
        pic.mime = "image/jpeg"
        pic.width = 800
        pic.height = 800
        audio.add_picture(pic)

        audio.save()
