from requests import get
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from os import path, mkdir, environ

MINI_PATH = "mini"
FULL_PATH = "full"
SITE_URL = "https://brawlhalla.com"
API_URL = "https://api.brawlhalla.com"
API_KEY = None


def scrape_full_image(full_path, link):
    if path.exists(full_path):
        return
    bs = BeautifulSoup(get(link).text, "html.parser")

    image = bs.find("img", {"class": "splash"})
    image_link = image.attrs["src"]

    request = get(image_link, stream=True)
    request.raise_for_status()

    with open(full_path, "wb") as f:
        for chunk in request.iter_content(1024):
            f.write(chunk)


if __name__ == "__main__":

    load_dotenv()

    if "API_KEY" in environ:
        API_KEY = environ["API_KEY"]
    else:
        raise RuntimeError("API_KEY is not set")

    if not path.exists(MINI_PATH):
        mkdir(MINI_PATH)

    if not path.exists(FULL_PATH):
        mkdir(FULL_PATH)

    legends = get(f"{API_URL}/legend/all", params={"api_key": API_KEY}).json()

    bs = BeautifulSoup(
        get(f"{SITE_URL}/legends").content.decode("utf-8"), "html.parser"
    )

    for legend, tag in zip(
        legends,
        filter(
            lambda a: "href" in a.attrs and a.attrs["href"].startswith("/legends/"),
            bs.find_all("a"),
        ),
    ):
        image_link = tag.find("img").attrs["src"]
        filename = f"{legend.get('legend_name_key')}.png"
        full_path = path.join(MINI_PATH, filename)

        scrape_full_image(
            path.join(FULL_PATH, filename), f"{SITE_URL}{tag.attrs['href']}"
        )

        if path.exists(full_path):
            continue

        request = get(image_link, stream=True)
        request.raise_for_status()

        with open(full_path, "wb") as f:
            for chunk in request.iter_content(1024):
                f.write(chunk)
