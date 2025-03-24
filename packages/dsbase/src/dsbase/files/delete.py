# pylint: disable=too-many-branches
from __future__ import annotations

from pathlib import Path

from send2trash import send2trash

from dsbase.shell import confirm_action
from dsbase.text import ColorName, print_colored


def delete_files(
    file_paths: str | Path | list[str] | list[Path] | list[str | Path],
    show_output: bool = True,
    show_individual: bool = True,
    show_total: bool = True,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Safely move a list of files to the trash. If that fails, asks for confirmation and
    deletes them directly.

    Args:
        file_paths: The file paths to delete.
        show_output: Whether to print output. (This overrides show_individual and show_total.)
        show_individual: Whether to print output for each individual file.
        show_total: Whether to print the total number of files deleted at the end.
        dry_run: Whether to do a dry run (don't actually delete).

    Returns:
        The number of successful deletions and failed deletions.
    """
    if dry_run and show_output:
        print_colored("NOTE: Dry run, not actually deleting!", "yellow")

    if not isinstance(file_paths, list):
        file_paths = [file_paths]

    successful_deletions, failed_deletions = 0, 0

    for file_path_str in file_paths:
        file_path = Path(file_path_str)
        if not file_path.exists():
            failed_deletions += 1
            if show_individual and show_output:
                print_colored(f"\nFile {file_path.name} does not exist.", "yellow")
            continue

        if _handle_file_deletion(
            file_path, dry_run=dry_run, show_output=show_individual and show_output
        ):
            successful_deletions += 1
        else:
            failed_deletions += 1

    if show_total and show_output and not dry_run:
        message = f"{successful_deletions} file{'s' if successful_deletions != 1 else ''} trashed."
        color: ColorName = "green" if successful_deletions > 0 else "red"
        if failed_deletions > 0:
            message += (
                f" Failed to delete {failed_deletions} file{'s' if failed_deletions != 1 else ''}."
            )
        print_colored(message, color)

    return successful_deletions, failed_deletions


def _handle_file_deletion(file_path: Path, dry_run: bool = False, show_output: bool = True) -> bool:
    """Attempt to delete a single file, sending it to trash or permanently deleting it.

    Args:
        file_path: The path of the file to delete.
        dry_run: Whether to perform a dry run.
        show_output: Whether to print output messages.

    Returns:
        True if the deletion was successful, False otherwise.
    """
    try:
        if dry_run:
            if show_output:
                print_colored(f"Would delete: {file_path}", "cyan")
            return True

        send2trash(str(file_path))
        if show_output:
            print_colored(f"✔ Trashed {file_path.name}", "green")
        return True
    except Exception as e:
        if show_output:
            print_colored(f"\nFailed to send file to trash: {e}", "red")
        if confirm_action("Do you want to permanently delete the file?"):
            try:
                file_path.unlink()
                if show_output:
                    print_colored(f"✔ Permanently deleted {file_path.name}", "green")
                return True
            except OSError as err:
                if show_output:
                    print_colored(
                        f"\nError: Failed to permanently delete {file_path.name} : {err}", "red"
                    )
    return False
