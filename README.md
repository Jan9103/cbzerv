# CBZerv

A lightweight webserver for viewing mangas/ comics stored on a linux/ bsd server.

## Features:

* Tag based search (with exclude support) (`tagfile.txt`)
* Directory preview pictures (`folder.extension`)
* No restriction on file-structure
* Cbz and Pdf support
* Phone-view support
* Low resource usage
* Hackable
   * Support for custom `index.html` files at any level (as well as accompanying css/.. files)
   * Usable with a reverse proxy
* Support for `.ignore` files
* Support for `.ff.bz2` images within `cbz` (requires ImageMagick7 to be installed)

## Usage:

### Executable

```sh
PORT=8080 python3 cbzerv.py
```

Just execute it with [python3](https://python.org).

Configuration (environmental variables):
* `PORT`: which port should be used (default: `8080`)
* `PWD` (aka `current working directory`): the base directory

### Filestructure

It can be structured however you want.

However: it is recommended to put each manga/comic into its own directory even if it has just one chapter.

Also: there are a few files with special meanings:
* `tagfile.txt`: a list of tags, which apply to a directory (manga/comic). One tag per line.
* `folder.png`, `folder.jpg`, etc: a picture representing the directory (example: cover, author-picture, etc)
* `.ignore`: do not include contents of this directory in listings or searches.
* `index.html`: override the listing of a directory with a custom one.

And comics/mangas should have a `.cbz` or `.pdf` file extension.

Example filestructure:
```
cbzerv.py
cbzerv
|- Marvel
|  |- folder.png
|  |- Spiderman
|     |- tagfile.txt
|     |- folder.jpg
|     |- Episode1.cbz
|     |- Episode2.pdf
|- Manga
   |- Izumi Tomoki      # <-- author
   |  |- Mieruko-chan
   |     |- tagfile.txt
   |     |- Ch 01.cbz
   |     |- Ch 02.cbz
   |- Tower of God
      |- Book 001.cbz
```

Example `tagfile.txt` contents:
```
Comedy
Slice of Life
Vampires
Shounen
Japanese
```

## Scripts included

* `downloader/guya.py`: Synchronise all (or specific) mangas from [Guya][] instances (should also support most guya-forks). (usage: `python3 downloader/guya --help`)
* `downloader/peppercarrot.py`: Download <https://www.peppercarrot.com>.
* `tools/cbz_optimizer.nu`: Try to reduce the `cbz` filesize without loosing data. (usage: `nu tools/cbz_optimizer.nu --help`)

## Performance

Test environment:
* Raspberry Pi 4
* 32985 cbz files
* 1740 tagfiles

### Resource Usage

Over 3 days including a lot of reading (measured using systemd):
* 49.921s CPU time
* RAM:
  * idle after 3 days: 10.0M + 11.1M swap
  * peak: 462.3M + 13.9M swap

### Speed

Searching all files by tag (measured via firefox devtools):
* after wiping cache: about 370ms
* with intact cache: about 200ms

[Guya]: https://github.com/subject-f/guyamoe
