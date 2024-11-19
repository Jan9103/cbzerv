import requests
from tempfile import TemporaryDirectory
from os import path, mkdir
from bs4 import BeautifulSoup
from zipfile import ZipFile
from typing import List


def main() -> None:
    basedir: str = path.abspath("./peppercarrot")
    mkdir(basedir)
    for chapter_url in list_chapter_urls():
        cbz_name: str = path.join(basedir, path.basename(chapter_url.split("#")[0].split("?")[0].removesuffix(".html")) + ".cbz")
        if not path.exists(cbz_name):
            download_chapter(chapter_url, cbz_name)


def list_chapter_urls() -> List[str]:
    response: requests.Response = requests.get("https://www.peppercarrot.com/en/webcomics/index.html")
    response.raise_for_status()
    soup: BeautifulSoup = BeautifulSoup(response.content, features="html.parser")
    return [i.find("a").attrs.get("href") for i in soup.find_all("figure", class_="thumbnail")]


def download_chapter(url: str, target_cbz_file: str) -> None:
    assert not path.exists(target_cbz_file), f"CBZ file {target_cbz_file} already exists."
    response: requests.Response = requests.get(url)
    response.raise_for_status()
    soup: BeautifulSoup = BeautifulSoup(response.content, features="html.parser")
    with ZipFile(target_cbz_file, "w", compresslevel=9) as cbz:
        for comicpage in soup.find_all("img", class_="comicpage"):
            image_url: str = comicpage.attrs.get("src")
            image_name: str = path.basename(image_url.split("?")[0].split("#")[0])
            image_response: requests.Response = requests.get(image_url)
            response.raise_for_status()
            cbz.writestr(image_name, image_response.content)


if __name__ == "__main__":
    main()
