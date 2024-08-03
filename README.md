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

## Usage:

```sh
PORT=8080 python3 cbzerv.py
```

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

## Alternatives

* [Komga](https://komga.org/): High resource usage (3-20% cpu idle on my pi), but nicer UI
* [Mihon](https://github.com/mihonapp/mihon) and forks: Android app (-> on device) with builtin downloader
