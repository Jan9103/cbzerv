# CBZerv

My personal minimal Comic-Book-Zip/PDF Server for use within my intranet.

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
   |     |- Ch 01.cbz
   |     |- Ch 02.cbz
   |- Tower of God
   |  |- Book 001.cbz
   |- Yuri              # <-- genre
   |  |- Bloom into you (complete).pdf
   |- Random Oneshot.cbz
```

Note: i have no idea if it works outside of UNIX-like OS.

