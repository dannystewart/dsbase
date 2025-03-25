# Evanescence Remix Downloader

The official versions of my remixes are the ones published [on my website](https://music.dannystewart.com/evanescence/), so this script grabs them from there. [`evtracks.json`](https://github.com/dannystewart/dsbase/blob/main/packages/evremixes/evtracks.json) holds the current list of available remixes, metadata, and URLs.

You're presented with the choice of FLAC or ALAC (Apple Lossless), as well as where you want the files to be saved. The default options are your Downloads and Music folders, but you can also enter a custom path. After downloading, it will apply the correct metadata, album art, and filenames.

Install via `pip install evremixes` and then `evremixes` to run the script.
