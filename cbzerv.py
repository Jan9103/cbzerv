from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional, List, TypeVar, Dict, Set
from os import path, listdir, environ, walk
from zipfile import ZipFile
from urllib.parse import urlparse, parse_qs, ParseResult, unquote
from functools import lru_cache
import html

# common mimes used by hand
MIME_JS = "text/javascript"
MIME_JSON = "application/json"
MIME_HTML = "text/html; charset=utf-8"
MIME_TEXT = "text/text"
MIME_PDF = "application/pdf"
# all supported mimes
FILE_EXT_TO_MIME: Dict[str, str] = {
    "css": "text/css",
    "gif": "image/gif",
    "html": MIME_HTML,
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "js": MIME_JS,
    "json": MIME_JSON,
    "pdf": MIME_PDF,
    "png": "image/png",
    "svg": "image/svg+xml",
    "txt": MIME_TEXT,
    "webp": "image/webp",
}
IMAGE_FILE_EXTENSIONS: List[str] = [
    "gif",
    "jpeg",
    "jpg",
    "png",
    "svg",
    "webp",
]

HTML_HEAD: str = '''
<!DOCTYPE HTML><html><head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        html,body{height:100%;margin:0;background-color:black;color:white;}
        a{color:cyan;}a:visited{color:orange;}
        img{max-width:100%;}
        ul>li>a>img{max-width:80%;max-height:300px;}
        ul{column-width:300px;column-count:auto;list-style-type:none;}
    </style></head><body>
'''
HTML_TAIL: str = '</body></html>'

CLEAR_CACHE_PATH: str = "/clear_serverside_cache"


class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        self.send_response(501)  # Not Implemented
        self.send_header("Content-Type", MIME_TEXT)
        self.end_headers()
        self.wfile.write(b'POST is not supported')

    def do_GET(self) -> None:
        parsedurl = urlparse(self.path)
        if (parsedurl.path == CLEAR_CACHE_PATH):
            read_tagfile.cache_clear()
            self.send_response(200)
            self.send_header("Content-Type", MIME_HTML)
            self.end_headers()
            self.wfile.write(
                f'{HTML_HEAD}Cleared cache <a href="javascript:history.back()">Back</a>{HTML_TAIL}'
                .encode(encoding="utf-8", errors="replace")
            )
            return
        target_file: str = path.realpath(path.join(path.curdir, unquote(parsedurl.path.lstrip("/"))))
        if not target_file.startswith(path.abspath(path.curdir)):
            self.send_response(403)
            self.end_headers()
            return
        if (parsedurl.path.endswith("/query")):
            self.handle_query(parsedurl, target_file)
            return

        if not path.isfile(target_file):
            if path.isfile(path.join(target_file, "index.html")):
                self.send_response(307)
                self.send_header("Location", f"{parsedurl.path}/index.html")
                self.end_headers()
                return
            self.send_index(target_file, parsedurl)
            return

        file_ext: str = path.splitext(target_file)[1].lstrip(".").lower()

        mime: Optional[str] = get_mime(file_ext)

        if mime is None:
            if file_ext == "cbz":
                self.send_cbz(target_file, parsedurl)
                return
            if file_ext == "pdf":
                self.send_pdf(target_file, parsedurl)
                return
            self.return_unsupported_mime(file_ext)
            return

        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.end_headers()
        with open(target_file, "rb") as f:
            self.wfile.write(f.read())

    def send_pdf(self, file: str, parsedurl: ParseResult) -> None:
        query = parse_qs(parsedurl.query)
        if query:
            self.send_response(200)
            self.send_header("Content-Type", MIME_PDF)
            self.end_headers()
            with open(file, "rb") as f:
                self.wfile.write(f.read())
            return
        self.send_response(200)
        self.send_header("Content-Type", MIME_HTML)
        self.end_headers()
        thisurl = html.escape(parsedurl.path)
        # https://www.w3docs.com/snippets/html/how-to-embed-pdf-in-html.html
        # https://www.w3docs.com/snippets/html/how-to-make-a-div-fill-the-height-of-the-remaining-space.html
        self.wfile.write(f'''
            {HTML_HEAD}<div style="display:flex;flex-flow:column;height:100%">
                <h1 style="flex:0 1 auto">{generate_html_pathstr(unquote(parsedurl.path))}</h1>
                <object data="{thisurl}?file=true" type="application/pdf" width="100%" style="flex:1 1 auto">
                    <p>Unable to display PDF file. <a href="{thisurl}?file=true">Download</a> instead.</p>
                </object>
            </div>{HTML_TAIL}
        '''.encode(encoding="utf-8", errors="replace"))

    def send_cbz(self, file: str, parsedurl: ParseResult) -> None:
        query = parse_qs(parsedurl.query)
        if "image" in query:
            imagefile: str = query["image"] if isinstance(query["image"], str) else query["image"][0]
            image_extension: str = path.splitext(imagefile)[1].lstrip(".")
            image_mime: Optional[str] = get_mime(image_extension)
            if image_mime is None:
                self.return_unsupported_mime(image_extension)
                return
            self.send_response(200)
            self.send_header("Content-Type", image_mime)
            self.end_headers()
            try:
                with ZipFile(file, "r") as zip_ref:
                    self.wfile.write(zip_ref.read(imagefile))
            except PermissionError:
                # i dont see a easy way to return a error as image without extensive libs or storing it to RAM
                pass
            return

        images: List[str] = []
        try:
            with ZipFile(file, "r") as zip_ref:
                images = [
                    i.filename
                    for i in zip_ref.filelist
                    if get_index(i.filename.rsplit(".", 1), 1) in IMAGE_FILE_EXTENSIONS
                ]
        except PermissionError:
            self.send_response(500)
            self.send_header("Content-Type", MIME_TEXT)
            self.end_headers()
            self.wfile.write(b'Unable to display file: server has insufficient permissions to read it')
            return
        self.send_response(200)
        self.send_header("Content-Type", MIME_HTML)
        self.end_headers()
        images.sort()
        thispath = html.escape(parsedurl.path)

        # calculate next chapter
        dir, filename = path.split(file)
        dircontent: List[str] = listdir(dir)
        dircontent.sort()
        index_of_this: int = dircontent.index(filename)
        next_chapter: Optional[str] = None
        if len(dircontent) > index_of_this + 1:
            next_chapter = dircontent[index_of_this + 1]

        self.wfile.write(f'''
            {HTML_HEAD}
                <style>body{{margin-left:auto;margin-right:auto;width:fit-content;}}</style>
                <h1>{generate_html_pathstr(unquote(parsedurl.path))}</h1>
                {"<br>".join([f'<img src="{thispath}?image={html.escape(i)}">' for i in images])}
                {f'<br><a href="{html.escape(next_chapter)}">{html.escape(next_chapter)}</a>' if next_chapter else ""}
            {HTML_TAIL}
        '''.encode(encoding="utf-8", errors="replace"))

    def handle_query(self, parsedurl: ParseResult, target_file: str) -> None:
        query_string: Dict[str, List[str]] = parse_qs(parsedurl.query)
        if not query_string:
            self.send_query_page(parsedurl)
            return
        wanted: List[str] = [k.strip() for k, v in query_string.items() if "wanted" in v]
        unwanted: List[str] = [k.strip() for k, v in query_string.items() if "unwanted" in v]
        del query_string
        tagfiles: List[str] = find_all_tagfile_paths(path.relpath(target_file[:-6]))
        matching_dirs: List[str] = []
        for tagfile in tagfiles:
            tags = read_tagfile(tagfile)
            if any((tag in unwanted for tag in tags)):
                continue
            # any is faster than all -> inverse
            if any((wanted_tag not in tags for wanted_tag in wanted)):
                continue
            matching_dirs.append(tagfile.rsplit("/", 1)[0])
        self.send_response(200)
        self.send_header("Content-Type", MIME_HTML)
        self.end_headers()
        files_html: List[str] = []
        for dir_path in matching_dirs:
            html_path: str = html.escape(path.relpath(dir_path, path.curdir))
            dir_picture: str = next((
                f'<img src="{html_path}/{img_file_name}">'
                for img_file_name in (f"folder.{i}" for i in IMAGE_FILE_EXTENSIONS)
                if path.isfile(f"{dir_path}/{img_file_name}")
            ), "")
            files_html.append(f'<li><a href="{html_path}">{dir_picture}{html_path}</a></li>')
        files_html.sort()
        self.wfile.write(f'''
            {HTML_HEAD}
                <nav><a href="javascript:window.history.back();">Back</a></nav>
                <h1>Search Results within {generate_html_pathstr(parsedurl.path[:-6])}</h1>
                <ul>{"".join(files_html)}</ul>
            {HTML_TAIL}
        '''.encode(encoding="utf-8", errors="replace"))

    def send_query_page(self, parsedurl: ParseResult) -> None:
        self.send_response(200)
        self.send_header("Content-Type", MIME_HTML)
        self.end_headers()
        tagfiles: List[str] = find_all_tagfile_paths()
        tags: Set[str] = set()
        for filepath in tagfiles:
            tags.update(read_tagfile(filepath))
        escaped_tags: List[str] = [html.escape(i) for i in tags]
        escaped_tags.sort()
        del tags
        tags_html: str = "".join((
            f'''
            <tr>
                <td><input type="radio" name="{tag}" value="ignore" checked="checked"></td>
                <td><input type="radio" name="{tag}" value="wanted"></td>
                <td><input type="radio" name="{tag}" value="unwanted"></td>
                <td>{tag}</td>
            </tr>
            '''
            for tag in (html.escape(i) for i in escaped_tags) if tag
        ))
        self.wfile.write(f'''
            {HTML_HEAD}
                <nav><a href="javascript:window.history.back();">Back</a></nav>
                <h1>Search within {generate_html_pathstr(parsedurl.path[:-6])}</h1>
                <form action="{html.escape(parsedurl.path)}">
                    <table>
                        <tr><th>Allow</th><th>Enforce</th><th>Block</th><th>Tag</th></tr>
                        {tags_html}
                    </table>
                    <input type="submit" value="Search">
                </form>
                <form action="{CLEAR_CACHE_PATH}">
                    <input type="submit" value="Clear serverside cache">
                </form>
            {HTML_TAIL}
        '''.encode(encoding="utf-8", errors="replace"))

    def return_unsupported_mime(self, extension: str) -> None:
        self.send_response(415)  # unsupported media type
        self.send_header("Content-Type", MIME_TEXT)
        self.end_headers()
        self.wfile.write(f"file extension {extension} is not supported.".encode(encoding="utf-8", errors="replace"))

    def send_index(self, target_file: str, parsedurl: ParseResult) -> None:
        files: List[str] = []
        thispath = html.escape(parsedurl.path)
        if path.isdir(target_file):
            try:
                raw_files: List[str] = listdir(target_file)
            except PermissionError:
                self.send_response(500)
                self.send_header("Content-Type", MIME_TEXT)
                self.end_headers()
                self.wfile.write(b'Unable to generate directory index: server is missing read and/or list permissions.')
                return
            for file in raw_files:
                dir_picture: str = next((
                    f'<img src="{thispath}/{html.escape(file)}/{img_file_name}">'
                    for img_file_name in (f"folder.{i}" for i in IMAGE_FILE_EXTENSIONS)
                    if path.isfile(f"{target_file}/{file}/{img_file_name}")
                ), "") if path.isdir(f"{target_file}/{file}") else ""
                files.append(f'<li><a href="{thispath}/{html.escape(file)}">{dir_picture}{html.escape(file)}</a></li>')
            files.sort()
        self.send_response(200)
        self.send_header("Content-Type", MIME_HTML)
        self.end_headers()
        self.wfile.write(f'''
            {HTML_HEAD}
                <nav><a href="query">Query</a></nav>
                <h1>{generate_html_pathstr(unquote(parsedurl.path))}</h1>
                <ul>{"".join(files)}</ul>
            {HTML_TAIL}
        '''.encode(encoding="utf-8", errors="replace"))

@lru_cache
def read_tagfile(tagfile: str) -> List[str]:
    with open(tagfile, "r") as file_handle:
        lines = file_handle.readlines()
    return [tag.strip() for tag in lines]

def generate_html_pathstr(filepath: str) -> str:
    result: List[str] = []
    while True:
        p = filepath.rsplit("/", 1)
        if len(p) < 2 or not p[1]:
            result.reverse()
            return "".join(result)
        result.append(f'/<a href="{html.escape(filepath)}">{html.escape(p[1])}</a>')
        filepath = p[0]

def find_all_tagfile_paths(basedir: Optional[str] = None) -> List[str]:
    return [
        path.join(subdir, filename)
        for subdir, _, files in walk(basedir or path.curdir)
        for filename in files
        if filename == "tagfile.txt"
    ]

def get_mime(extension: str) -> Optional[str]:
    return FILE_EXT_TO_MIME.get(extension.lower(), None)

T = TypeVar('T')
def get_index(l: List[T], idx: int) -> Optional[T]:
    return l[idx] if len(l) > idx else None

def main(port: int) -> None:
    server: HTTPServer = HTTPServer(("", port), RequestHandler)
    server.serve_forever()

if __name__ == "__main__":
    main(int(environ.get("PORT", "8080")))
