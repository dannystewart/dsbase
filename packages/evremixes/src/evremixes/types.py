from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class AudioFormat(StrEnum):
    """File format choices."""

    FLAC = "flac"
    ALAC = "m4a"

    @property
    def menu_choice(self) -> str:
        """Return the display name for the format."""
        return "FLAC" if self == AudioFormat.FLAC else "ALAC (Apple Lossless)"

    @property
    def display_name(self) -> str:
        """Return the display name for the format."""
        return self.name.upper()

    @property
    def extension(self) -> str:
        """Return the file extension for the format."""
        return self.value


class TrackVersions(StrEnum):
    """Choices for which track set to download."""

    ORIGINAL = "Original versions"
    INSTRUMENTAL = "Instrumental versions"
    BOTH = "Both sets"


class DownloadLocation(StrEnum):
    """Choices for download location."""

    DOWNLOADS = "Downloads folder"
    MUSIC = "Music folder"
    ONEDRIVE = "OneDrive folder"
    CUSTOM = "Custom path"


@dataclass
class AlbumInfo:
    """Full metadata for an album (track set)."""

    album_name: str
    album_artist: str
    artist_name: str
    genre: Literal["Electronic"]
    year: int
    cover_art_url: str
    inst_art_url: str
    tracks: list[TrackMetadata]


@dataclass
class TrackMetadata:
    """Metadata for a single track."""

    track_name: str
    file_url: str
    inst_url: str
    start_date: str
    track_number: int
