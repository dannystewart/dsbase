# dsbase

This is a delightful Python utility library that brings power and personality to your toolkit.

It contains various helpers refined through years of practical development, including an elegant logger, an environment variable manager, a path helper, database interfaces, file and media processing, and various other helpers that make common tasks a little easier or more joyful. Developed for personal use, but always to high standards of quality and flexibility.

**Note:** This library is constantly growing and evolving, so for stability you may want to pin specific versions for now. I try to be careful about breaking changes but development is still very active.

## Features

Some of the features include:

- `LocalLogger` for elegant and sophisticated logging that you'll love
- `EnvManager` for clear setup and access to environment variables
- `PathKeeper` for convenient cross-platform access to common paths
- Thread-safe `Singleton` metaclass for use in any project
- Drop-in `argparse` replacement with easier formatting
- Simple helper for comparing files and showing diffs
- Database helper interfaces for MySQL and SQLite
- Helpers for highly customizable copying, deleting, and listing of files
- Media helpers for audio and video transcoding using `ffmpeg`
- Notification helpers for email and Telegram
- Simple progress indicators and helpers for common shell tasks
- Loading animations that are both simple and charming
- Comprehensive collection of text manipulation tools
- Various time parsers and utilities, including a time-aware logger

## Installation

This is a monorepo containing a number of my packages. To install the main `dsbase` library:

```bash
pip install dsbase
```

To install my various other scripts from the `packages` directory:

```bash
pip install dsbin      # My script collection
pip install dsupdater  # My OS and software updater
pip install evremixes  # My remix downloader
pip install iplooker   # My IP lookup script
pip install pybumper   # My Python version bumper
pip install workcalc   # My work time spent calculator
```
