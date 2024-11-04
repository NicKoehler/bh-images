from os import path, mkdir
from requests import get
from bs4 import BeautifulSoup

MINI_PATH = "mini"
FULL_PATH = "full"
URL = "https://brawlhalla.com"


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
    bs = BeautifulSoup(get(f"{URL}/legends").content.decode("utf-8"), "html.parser")

    if not path.exists(MINI_PATH):
        mkdir(MINI_PATH)

    if not path.exists(FULL_PATH):
        mkdir(FULL_PATH)

    for tag in filter(
        lambda a: "href" in a.attrs and a.attrs["href"].startswith("/legends/"),
        bs.find_all("a"),
    ):
        image_link = tag.find("img").attrs["src"]
        filename = f"{tag.find('h3').text.lower()}.png".replace("ö", "o")
        full_path = path.join(MINI_PATH, filename)
        scrape_full_image(path.join(FULL_PATH, filename), f"{URL}{tag.attrs['href']}")

        if path.exists(full_path):
            continue

        request = get(image_link, stream=True)
        request.raise_for_status()

        with open(full_path, "wb") as f:
            for chunk in request.iter_content(1024):
                f.write(chunk)
