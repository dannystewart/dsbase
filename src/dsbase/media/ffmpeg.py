from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from pathlib import Path

from dsbase.shell.progress import halo_progress
from dsbase.text import color, print_colored


def run_ffmpeg(
    command: list[str],
    input_file: str,
    show_output: bool,
    output_filename: str | None = None,
) -> None:
    """Run a given ffmpeg command and handle progress display and errors.

    Args:
        command: The ffmpeg command to execute.
        input_file: The path to the input file.
        show_output: Whether to display output.
        output_filename: The name of the output file to show when converting. Defaults to None, in
            which case the input filename is used instead.

    Raises:
        RuntimeError: If the ffmpeg command fails.
    """
    spinner_messages = {
        "start": "Converting",
        "end": "Converted",
        "fail": "Failed to convert",
    }

    with halo_progress(
        output_filename or Path(input_file).name,
        start_message=spinner_messages["start"],
        end_message=spinner_messages["end"],
        fail_message=spinner_messages["fail"],
        show=show_output,
    ) as spinner:
        try:
            subprocess.run(command, check=True, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError as e:
            error_message = f"Error converting file '{input_file}'. Command '{' '.join(command)}' exited with status {e.returncode}. Error output:\n{e.stderr}"
            if spinner is not None:
                spinner.fail(color(error_message, "red"))
            else:
                print_colored(error_message, "red")
            raise RuntimeError(error_message) from e
        except Exception as e:
            if spinner is not None:
                spinner.fail(color(f"Unexpected error: {e}", "red"))
            else:
                print_colored(f"Unexpected error: {e}", "red")
            raise


def construct_filename(
    input_file: str | Path,
    output_file: str | Path | None,
    output_format: str | Path,
    input_files: list[str],
) -> str:
    """Construct the output filename based on the input file and the output format.

    Args:
        input_file: The path to the input file.
        output_file: The path to the output file. Defaults to None.
        output_format: The desired output format.
        input_files: A list of input files.

    Returns:
        The output filename.
    """
    input_path = Path(input_file)
    if not output_file:
        return f"{input_path.stem}.{output_format}"

    output_path = Path(output_file)
    final_output = (
        output_file
        if len(input_files) == 1
        else f"{output_path.stem}_{input_path.name}{output_path.suffix}"
    )
    return str(final_output)


def construct_ffmpeg_command(input_file: str, overwrite: bool) -> list[str]:
    """Construct the base ffmpeg command.

    Args:
        input_file: The path to the input file.
        overwrite: Whether to overwrite the output file if it already exists.
    """
    command = ["ffmpeg"]
    if overwrite:
        command += ["-y"]
    command += [
        "-nostdin",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        input_file,
    ]
    return command


def get_stream_info(file_path: str) -> dict[str, dict[dict[str, str], str]]:
    """Get stream information from the input file."""
    command = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", file_path]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    return json.loads(result.stdout)


def has_video_stream(file_path: str) -> bool:
    """Check if the file has a video stream (potentially cover art)."""
    stream_info = get_stream_info(file_path)
    return any(stream["codec_type"] == "video" for stream in stream_info["streams"])


def add_audio_flags(
    command: list[str],
    codec: str,
    output_format: str,
    audio_bitrate: str | None = None,
    sample_rate: str | None = None,
    bit_depth: int | None = None,
    preserve_metadata: bool = False,
    input_file: str | None = None,
) -> None:
    """Add the necessary flags for the desired audio codec settings to the ffmpeg command.

    Args:
        command: The ffmpeg command to which to apply the settings.
        codec: The desired codec. Defaults to None.
        output_format: The desired output format.
        audio_bitrate: The desired audio bitrate. Defaults to None.
        sample_rate: The desired sample rate. Defaults to None.
        bit_depth: The desired bit depth. Defaults to None.
        preserve_metadata: Whether to preserve existing metadata. Defaults to False.
        input_file: The path to the input file. Needed for checking video streams. Defaults to None.
    """
    if output_format == "m4a" and not codec:
        codec = "alac"

    if preserve_metadata:
        command.extend(["-map_metadata", "0"])
        if input_file and has_video_stream(input_file):
            command.extend(["-map", "0:v", "-c:v", "copy"])
        command.extend(["-map", "0:a"])
    else:
        command.append("-vn")

    if codec:
        command += ["-acodec", codec]
    else:
        codec_to_format = {
            "mp3": "libmp3lame",
            "wav": "pcm_s16le",
            "flac": "flac",
            "m4a": "alac",  # Default to ALAC for m4a
        }
        command += ["-acodec", codec_to_format.get(output_format, "copy")]

    if audio_bitrate:
        command += ["-b:a", audio_bitrate]

    if sample_rate:
        command += ["-ar", sample_rate]

    command.extend(_get_arguments_for_codec(output_format, bit_depth))


def _get_arguments_for_codec(output_format: str, bit_depth: int | None) -> list[str]:
    """Get the additional arguments needed specifically for the output format and bit depth."""
    command = []
    if output_format == "flac":
        command += ["-compression_level", "12"]
        command += ["-sample_fmt", "s16"]
    elif output_format == "m4a":
        if bit_depth:
            command += ["-bits_per_raw_sample", str(bit_depth)]
    elif output_format in {"wav", "aif", "aiff"}:
        if bit_depth in {16, 24, 32}:
            sample_format_mappings = {
                16: "s16",
                24: "s24",
                32: "s32",
            }
            sample_format = sample_format_mappings.get(bit_depth, "s16")
            command += ["-sample_fmt", sample_format]
    return command


def add_video_flags(
    command: list[str],
    video_codec: str,
    video_bitrate: str,
    audio_codec: str,
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


def ensure_lossless_first(input_files: list[str]) -> list[str]:
    """If there are multiple files with the same name, this function will sort the list such that
    uncompressed and lossless files are prioritized over compressed and lossy files.

    Args:
        input_files: A list of input files.
    """
    file_groups = defaultdict(list)

    for file in input_files:
        file_path = Path(file)
        base_name = file_path.stem
        file_groups[base_name].append(str(file_path))

    prioritized_extensions = [".wav", ".aiff", ".aif", ".flac", ".m4a"]

    prioritized_files = []
    for files in file_groups.values():
        selected_file = None
        for ext in prioritized_extensions:
            for file in files:
                if file.lower().endswith(ext):
                    selected_file = file
                    break
            if selected_file:
                break
        if not selected_file:
            selected_file = files[0]
        prioritized_files.append(selected_file)
    return prioritized_files
