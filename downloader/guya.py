#!/usr/bin/env python3

# This is a script to (batch-) download chapters from a guya (https://github.com/subject-f/guyamoe) server
# This is obviously only meant for migrating your own instance or accessing official publishing sites

import requests
from zipfile import ZipFile
from typing import Optional, List
from time import sleep
from os import path, makedirs, unlink


IMAGE_URL_SCHEMES: List[str] = [
    "{website_domain}/media/manga/{series_slug}/chapters/{folder}/{group_id}/{image}",  # (fork-patch) https://github.com/milleniumbug/guyamoe
    "{website_domain}/media/manga/{series_slug}/{chapter_no}/{image}",  # from the offical documentation
]


def main(
    base_download_dir: str = "./cbzerv",
    website_domain: str = "https://localhost:8000",
    series_slugs: Optional[List[str]] = None,
    sleep_time_between_images: float = 0.1,
):
    if series_slugs is None:
        print("No series specified. Downloading all series.")
        series_slugs = get_all_series_slugs(website_domain)
        print(f"Found {len(series_slugs)} series.")

    for series_slug in series_slugs:
        download_series(base_download_dir, website_domain, series_slug, sleep_time_between_images)


def download_series(base_download_dir: str, website_domain: str, series_slug: str, sleep_time_between_images: float) -> None:
    print(f"Downloading {series_slug}..")
    response = requests.get(f"{website_domain}/api/series/{series_slug}")
    response.raise_for_status()
    data = response.json()
    series_dir: str = path.join(base_download_dir, series_slug)
    if not path.exists(series_dir):
        makedirs(series_dir, exist_ok=True)
    assert path.isdir(path.realpath(series_dir)), f"Cannot download {series_slug} since the target directory ({series_dir}) exists and is not a directory"
    # TODO: download cover. data["cover"] contains a absolute path without domain
    for chapter_no, chapter_data in data["chapters"].items():
        folder: Optional[str] = chapter_data.get("folder", None)
        target_cbz_file: str = path.join(series_dir, f"{chapter_no}.cbz")
        if path.exists(target_cbz_file):
            print(f"Skipped {series_slug}/{chapter_no} (file already existed)")
            continue
        print(f"Downloading {series_slug}/{chapter_no}..")
        group_id, images = next((group_id, images) for group_id, images in chapter_data["groups"].items() if len(images) > 0)
        try:
            with ZipFile(target_cbz_file, "w", compresslevel=9) as cbz:
                for image in images:
                    for image_url_scheme in IMAGE_URL_SCHEMES:
                        # TODO: cache which scheme works and try it first
                        image_url: str = image_url_scheme.format(
                            chapter_no=chapter_no,
                            folder=folder,
                            group_id=group_id,
                            image=image,
                            series_slug=series_slug,
                            website_domain=website_domain,
                        )
                        response = requests.get(image_url)
                        if response.status_code == 200:
                            break
                    else:
                        assert False, f"Failed to download image {image} for {series_slug}/{chapter_no} (none of the attempted image-url-schemes worked)"
                    # no need to read chunked. if a single image is to big for ram its not a usable manga anyway
                    cbz.writestr(image, response.content)
                    sleep(sleep_time_between_images)
        except Exception as orig_exc:
            try:
                unlink(target_cbz_file)  # if it failed the file is incomplete/broken
            except FileNotFoundError as e:
                pass
            raise orig_exc


def get_all_series_slugs(website_domain: str) -> List[str]:
    response = requests.get(f"{website_domain}/api/get_all_series/")
    response.raise_for_status()
    return [data["slug"] for name, data in response.json().items()]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        prog="guya-downloader.py",
        description="Download mangas from guya instances",
    )
    parser.add_argument("website_domain", help="Example: http://localhost")
    parser.add_argument("base_download_directory", help="Where to store the downloads? (the series-slug will be auto-appended). Example: ./cbzerv/manga")
    parser.add_argument("series_slugs", nargs="*", help="The slug(-s) of the series you want to download. It is the manga-name similar part of the reader-url. Example: steamboat-willie")
    parser.add_argument("--all-series", action="store_true", help="Download all series available on the website")
    parser.add_argument("--sleep-time-between-images", type=float, help="Sleep between image downloads for x seconds to prevent DOSing the website (or getting banned for it)", default=0.1)
    args = parser.parse_args()
    if args.all_series:
        main(
            base_download_dir=args.base_download_directory,
            website_domain=args.website_domain,
            series_slugs=None,
            sleep_time_between_images=args.sleep_time_between_images,
        )
    else:
        main(
            base_download_dir=args.base_download_directory,
            website_domain=args.website_domain,
            series_slugs=args.series_slugs,
            sleep_time_between_images=args.sleep_time_between_images,
        )
