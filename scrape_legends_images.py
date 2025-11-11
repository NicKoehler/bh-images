from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Iterable, Mapping

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
)
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
LEGENDS_DIR = BASE_DIR / "legends"
MINI_DIR = LEGENDS_DIR / "mini"
FULL_DIR = LEGENDS_DIR / "full"

SITE_URL = "https://brawlhalla.com"
API_URL = "https://api.brawlhalla.com"


def download_file(url: str, dest_path: Path) -> None:
    """Download a file from *url* and write it to *dest_path*."""
    log.debug("Downloading %s", url)
    resp = requests.get(url, stream=True, timeout=10)
    resp.raise_for_status()
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    with dest_path.open("wb") as fp:
        for chunk in resp.iter_content(chunk_size=8192):
            fp.write(chunk)


def fetch_json(url: str, params: Mapping[str, str] | None = None) -> dict:
    """Return JSON decoded from *url*."""
    log.debug("Fetching JSON from %s", url)
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def scrape_full_image(full_path: Path, page_url: str) -> None:
    """
    Download the full‑size splash image of a legend.

    The function will exit early if *full_path* already exists.
    """
    if full_path.exists():
        log.debug("Full image already present: %s", full_path)
        return

    soup = BeautifulSoup(requests.get(page_url, timeout=10).text, "html.parser")
    img_tag = soup.find("img", class_="splash")
    if not img_tag or not (src := img_tag.get("src")):
        raise ValueError(f"Could not find splash image on {page_url}")

    download_file(src, full_path)


def main() -> None:
    load_dotenv()
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise RuntimeError("Environment variable API_KEY is missing")

    log.info("Fetching legend list from API")
    legends: Iterable[dict] = fetch_json(f"{API_URL}/legend/all", {"api_key": api_key})

    log.info("Scraping website for legend thumbnails")
    soup = BeautifulSoup(
        requests.get(f"{SITE_URL}/legends", timeout=10).content.decode("utf-8"),
        "html.parser",
    )

    # Find all <a> tags that link to a legend page
    legend_links = [
        a for a in soup.find_all("a") if a.get("href", "").startswith("/legends/")
    ]

    for legend_meta, tag in zip(legends, legend_links):
        name_key = legend_meta["legend_name_key"]
        filename = f"{name_key}.png"

        mini_path = MINI_DIR / filename
        full_path = FULL_DIR / filename

        # Full image (splash)
        scrape_full_image(full_path, f"{SITE_URL}{tag['href']}")

        # Mini thumbnail
        if mini_path.exists():
            log.debug("Mini image already present: %s", mini_path)
            continue

        img_src = tag.find("img").get("src")
        download_file(img_src, mini_path)

    log.info("Scraping complete.")


if __name__ == "__main__":
    main()
