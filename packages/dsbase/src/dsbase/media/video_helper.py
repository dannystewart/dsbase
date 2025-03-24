from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from dsbase.media.media_manager import MediaManager


class VideoHelper:
    """A utility class with a comprehensive set of methods for video operations."""

    def __init__(self, media: MediaManager):
        self.media = media

    def ffmpeg_video(
        self,
        input_files: Path | list[Path],
        output_format: str,
        output_file: str | None = None,
        overwrite: bool = True,
        video_codec: str | None = None,
        video_bitrate: str | None = None,
        audio_codec: str | None = None,
        additional_args: list[str] | None = None,
        show_output: bool = False,
    ):
        """Convert a video file to a different format using ffmpeg with various options.

        Args:
            input_files: The path to the input file or a list of paths to input files.
            output_format: The desired output format.
            output_file: The path to the output file. Defaults to None.
            overwrite: Whether to overwrite the output file if it already exists. Defaults to True.
            video_codec: The desired video codec. Defaults to None, which uses "copy".
            video_bitrate: The desired video bitrate. Defaults to None.
            audio_codec: The desired audio codec. Defaults to None, which uses "copy".
            additional_args: List of additional arguments to pass to ffmpeg. Defaults to None.
            show_output: Whether to display ffmpeg output. Defaults to False.
        """
        if not isinstance(input_files, list):
            input_files = [input_files]

        for input_file in input_files:
            current_output_file = self.media.construct_filename(
                input_file,
                output_file,
                output_format,
                input_files,
            )
            command = self.media.construct_ffmpeg_command(input_file, overwrite)
            self.add_video_flags(command, video_codec, video_bitrate, audio_codec)

            if additional_args:
                command.extend(additional_args)

            command.append(current_output_file)
            self.media.run_ffmpeg(command, input_file, show_output)

    def has_video_stream(self, file_path: Path) -> bool:
        """Check if the file has a video stream (potentially cover art)."""
        stream_info = self.get_stream_info(file_path)
        return any(stream["codec_type"] == "video" for stream in stream_info["streams"])

    @staticmethod
    def add_video_flags(
        command: list[str],
        video_codec: str | None,
        video_bitrate: str | None,
        audio_codec: str | None,
    ) -> None:
        """Add the necessary flags for the desired video codec settings to the ffmpeg command.

        Args:
            command: The ffmpeg command to which to apply the settings.
            video_codec: The desired video codec. Defaults to None.
            video_bitrate: The desired video bitrate. Defaults to None.
            audio_codec: The desired audio codec. Defaults to None.
        """
        command += ["-c:v", video_codec] if video_codec else ["-c:v", "copy"]
        if video_bitrate:
            command += ["-b:v", video_bitrate]

        command += ["-c:a", audio_codec] if audio_codec else ["-c:a", "copy"]

    @staticmethod
    def get_stream_info(file_path: Path) -> dict[str, dict[dict[str, str], str]]:
        """Get stream information from the input file."""
        command = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", file_path]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        return json.loads(result.stdout)
