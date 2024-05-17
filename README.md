# CBZerv

My personal Comic-Book-Zip/PDF Server for use within my intranet.

NOTE: it does not work on Windows (file path separator not supported)

Usage:
```sh
PORT=8080 python3 cbzerv.py
```

There is no restriction on filestructure, but heres an example filestructure:
```
cbzerv.py
cbzerv                  # <-- base path for nginx revers-proxy
|- Marvel
|  |- folder.png        # <-- folder.ext is used as a directory thumbnail if present
|  |- Spiderman
|     |- tagfile.txt    # <-- newline seperated list of tags for this directory (ex: genres)
|     |- folder.jpg
|     |- Episode1.cbz
|     |- Episode2.cbz
|     |- Episode3.pdf
|- Manga
   |- index.html        # <-- custom index file
   |- my_style.css      # <-- for use in custom index
   |- manga-symbol.png  # <-- for use in custom index
   |- Izumi Tomoki      # <-- author
   |  |- Mieruko-chan
   |     |- tagfile.txt
   |     |- Ch 01.cbz
   |     |- Ch 02.cbz
   |- Tower of God
   |  |- Book 001.cbz
```
