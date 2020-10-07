#! /usr/bin/env python3

from .. import utils
import cloudscraper
from bs4 import BeautifulSoup
from itertools import count
import os
import re

requests = cloudscraper.create_scraper(allow_brotli=False)

@utils.json_cached("scan-fr.json")
def get_mangas():
    print("Fetching manga list from scan-fr: page ", end="", flush=True)
    mangas = {}
    for page in count(1):
        print(f"{page}, ", end="", flush=True)
        url = f"https://www.scan-fr.cc/filterList?page={page}&cat=&alpha=&sortBy=name&asc=true&author=&tag="
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")
        links = soup("a", class_="chart-title")
        if links is None:
            break
        seen = False
        for link in links:
            url = link["href"]
            title = link.text.lower()
            mangas[title] = url
            seen = True
        if not seen:
            break
    print("done")
    return mangas


def get_chapters(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    chapters = {}
    for link in soup.find_all("a"):
        url = link["href"]
        if "/manga/" not in url:
            continue
        num = float(url.rsplit("/", 1)[-1])
        chapters[num] = url
    return chapters

def download_chapter(url, path, loop):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    numbers = [int(opt["value"]) for opt in soup.find("select")("option")]

    urls = {}
    for img in soup("img"):
        url = img.get("data-src", "").strip()
        if "/uploads/" not in url:
            continue
        fname = url.rsplit('/', 1)[-1]
        urls[fname] = url

    os.makedirs(path, exist_ok=True)
    utils.download_urls(urls, path, loop, headers=requests.headers,
                        cookies=requests.cookies)
    for fname, url in urls.items():
        content = requests.get(url).content
        with open(os.path.join(path, fname), "wb") as f:
            f.write(content)
