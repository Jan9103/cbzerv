from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional, List
from os import path, listdir, environ
from zipfile import ZipFile
from urllib.parse import urlparse, parse_qs, ParseResult, unquote
import html

# https://wiki.selfhtml.org/wiki/MIME-Type/%C3%9Cbersicht
MIME_JS = "text/javascript"
MIME_JSON = "application/json"
MIME_HTML = "text/html; charset=utf-8"
MIME_TEXT = "text/text"
MIME_CSS = "text/css"
MIME_JPG = "image/jpeg"
MIME_PNG = "image/png"
MIME_SVG = "image/svg+xml"
MIME_GIF = "image/gif"
MIME_PDF = "application/pdf"

HTML_HEAD = '''
<!DOCTYPE HTML><html><head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        html,body{height:100%;margin:0;background-color:black;color:white;}
        a{color:cyan;}a:visited{color:orange;}
        img{max-width:100%;}
    </style></head><body>
'''
HTML_TAIL = '</body></html>'

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        self.send_response(501)  # Not Implemented
        self.send_header("Content-Type", MIME_TEXT)
        self.end_headers()
        self.wfile.write(b'POST is not supported')

    def do_GET(self) -> None:
        parsedurl = urlparse(self.path)
        target_file: str = path.realpath(path.join(path.curdir, unquote(parsedurl.path.lstrip("/"))))
        if not target_file.startswith(path.abspath(path.curdir)):
            self.send_response(403)
            self.end_headers()
            return

        if not path.isfile(target_file):
            if path.isfile(path.join(target_file, "index.html")):
                self.send_response(301)
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
            with ZipFile(file, "r") as zip_ref:
                self.wfile.write(zip_ref.read(imagefile))
            return
        self.send_response(200)
        self.send_header("Content-Type", MIME_HTML)
        self.end_headers()
        # TODO: cbz index
        images: List[str] = []
        with ZipFile(file, "r") as zip_ref:
            images = [i.filename for i in zip_ref.filelist if i.filename.rsplit(".", 1)[1] in ["png", "jpg", "jpeg", "gif", "svg"]]
        images.sort()
        thispath = html.escape(parsedurl.path)
        self.wfile.write(f'''
            {HTML_HEAD}
                <h1>{generate_html_pathstr(unquote(parsedurl.path))}</h1>
                {"<br>".join([f'<img src="{thispath}?image={html.escape(i)}">' for i in images])}
            {HTML_TAIL}
        '''.encode(encoding="utf-8", errors="replace"))

    def return_unsupported_mime(self, extension: str) -> None:
        self.send_response(415)  # unsupported media type
        self.send_header("Content-Type", MIME_TEXT)
        self.end_headers()
        self.wfile.write(f"file extension {extension} is not supported.".encode(encoding="utf-8", errors="replace"))

    def send_index(self, target_file: str, parsedurl: ParseResult) -> None:
        self.send_response(200)
        self.send_header("Content-Type", MIME_HTML)
        self.end_headers()
        files: List[str] = []
        thispath = html.escape(parsedurl.path)
        if path.isdir(target_file):
            files = [f'<li><a href="{thispath}/{html.escape(i)}">{html.escape(i)}</a></li>' for i in listdir(target_file)]
            files.sort()
        self.wfile.write(f'''
            {HTML_HEAD}
                <h1>{generate_html_pathstr(unquote(parsedurl.path))}</h1>
                <ul>{"".join(files)}</ul>
            {HTML_TAIL}
        '''.encode(encoding="utf-8", errors="replace"))
        return

def generate_html_pathstr(filepath: str) -> str:
    result: List[str] = []
    while True:
        p = filepath.rsplit("/", 1)
        if len(p) < 2 or not p[1]:
            result.reverse()
            return "".join(result)
        result.append(f'/<a href="{html.escape(filepath)}">{html.escape(p[1])}</a>')
        filepath = p[0]

def get_mime(extension: str) -> Optional[str]:
    extension = extension.lower()
    if extension in ("html", "htm"):
        return MIME_HTML
    if extension == "js":
        return MIME_JS
    if extension == "css":
        return MIME_CSS
    if extension == "json":
        return MIME_JSON
    if extension == "txt":
        return MIME_TEXT
    if extension in ("jpg", "jpeg"):
        return MIME_JPG
    if extension == "png":
        return MIME_PNG
    if extension == "gif":
        return MIME_GIF
    if extension == "svg":
        return MIME_SVG
    return None

def main(port: int) -> None:
    server: HTTPServer = HTTPServer(("", port), RequestHandler)
    server.serve_forever()

if __name__ == "__main__":
    main(int(environ.get("PORT", "8080")))
