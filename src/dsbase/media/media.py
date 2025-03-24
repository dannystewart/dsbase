"""Functions for working with media files using ffmpeg."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from dsbase.animate import conditional_walking
from dsbase.media.ffmpeg import (
    add_audio_flags,
    add_video_flags,
    construct_ffmpeg_command,
    construct_filename,
    ensure_lossless_first,
    run_ffmpeg,
)
from dsbase.text import print_colored

if TYPE_CHECKING:
    from pathlib import Path


def find_bit_depth(input_file: str | Path, show_animation: bool = False) -> int:
    """Identify the bit depth of an input audio file using ffprobe.
    Returns the bit depth of the input file, or 0 if the bit depth could not be determined.

    Args:
        input_file: The path to the input file.
        show_animation: Whether to show the loading animation. Defaults to False.
    """
    with conditional_walking(show_animation):
        bit_depth_command = (  # First, try to get the bit depth in the usual way
            f"ffprobe -v error -select_streams a:0 -show_entries stream=bits_per_raw_sample "
            f'-of default=noprint_wrappers=1:nokey=1 "{input_file}"'
        )
        bit_depth = subprocess.getoutput(bit_depth_command)
        if bit_depth.isdigit():
            return int(bit_depth)

        codec_command = (  # If that fails, try to extract the audio codec format
            f"ffprobe -v error -select_streams a:0 -show_entries stream=codec_name "
            f'-of default=noprint_wrappers=1:nokey=1 "{input_file}"'
        )
        codec = subprocess.getoutput(codec_command)
        if "pcm_s16" in codec:
            return 16
        if "pcm_s24" in codec:
            return 24
        if "pcm_s32" in codec:
            return 32

    print_colored(
        "Bit depth could not be determined. Skipping 24-bit conversion.",
        "yellow",
    )
    return 0


def ffmpeg_audio(
    input_files: str | list[str],
    output_format: str,
    output_file: str | None = None,
    overwrite: bool = True,
    codec: str | None = None,
    bit_depth: int | None = None,
    audio_bitrate: str | None = None,
    sample_rate: str | None = None,
    preserve_metadata: bool = False,
    additional_args: list[str] | None = None,
    show_output: bool = False,
    show_animation: bool = False,
) -> None:
    """Convert an audio file to a different format using ffmpeg with various options.
    Automatically prioritizes lossless formats over lossy formats.

    Args:
        input_files: The path to the input file or a list of paths to input files.
        output_format: The desired output format.
        output_file: The path to the output file. Defaults to None.
        overwrite: Whether to overwrite the output file if it already exists. Defaults to True.
        codec: The desired codec. Defaults to None.
        bit_depth: The desired bit depth. Defaults to 16.
        audio_bitrate: The desired audio bitrate. Defaults to None.
        sample_rate: The desired sample rate. Defaults to None.
        preserve_metadata: Whether to preserve existing metadata and album art. Defaults to False.
        additional_args: List of additional arguments to pass to ffmpeg. Defaults to None.
        show_output: Whether to display ffmpeg output. Defaults to False.
        show_animation: Whether to show the loading animation. Defaults to False.
    """
    if not isinstance(input_files, list):
        input_files = [input_files]

    input_files = ensure_lossless_first(input_files)

    for input_file in input_files:
        current_bit_depth = bit_depth or find_bit_depth(input_file, show_animation=show_animation)

        current_output_file = construct_filename(
            input_file,
            output_file,
            output_format,
            input_files,
        )
        command = construct_ffmpeg_command(input_file, overwrite)

        add_audio_flags(
            command,
            codec,
            output_format,
            audio_bitrate,
            sample_rate,
            current_bit_depth,
            preserve_metadata,
            input_file,
        )

        if additional_args:
            command.extend(additional_args)

        command.append(current_output_file)
        run_ffmpeg(command, input_file, show_output, current_output_file)


def ffmpeg_video(
    input_files: str | list[str],
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
        current_output_file = construct_filename(
            input_file,
            output_file,
            output_format,
            input_files,
        )
        command = construct_ffmpeg_command(input_file, overwrite)
        add_video_flags(command, video_codec, video_bitrate, audio_codec)

        if additional_args:
            command.extend(additional_args)

        command.append(current_output_file)
        run_ffmpeg(command, input_file, show_output)
