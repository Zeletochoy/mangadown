#! /usr/bin/env python3

from .. import utils
import cloudscraper
from bs4 import BeautifulSoup
from itertools import count
import os
import re

requests = cloudscraper.create_scraper(allow_brotli=False)

@utils.json_cached("japscan.json")
def get_mangas():
    print("Fetching manga list from japscan.com: page ", end="", flush=True)
    mangas = {}
    for page in count(1):
        print(f"{page}, ", end="", flush=True)
        url = f"http://www.japscan.se/mangas/{page}"
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")
        main = soup.find(id="main")
        if main is None:
            break
        for title_p in main.find(class_="d-flex").find_all("p"):
            link = title_p.find("a")
            url = link["href"]
            if url.startswith("/manga"):
                title = link.text.lower()
                if title in mangas:
                    # wraps to page 1
                    print("done")
                    return mangas
                mangas[title] = url

def get_chapters(url):
    base_url = "http://www.japscan.se"
    url = base_url + url
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    tab = soup.find(id="chapters_list")
    chapters = {}
    for chap in tab.find_all("a"):
        url = chap["href"]
        if url.startswith("/"):
            url = base_url + url
        if not url.endswith("/"):
            url += "/"
        if "lecture-en-ligne" in url:
            match = re.search("(\d+)(?!.*\d)", url)
            num = float(match.group(1))
            chapters[num] = url
    return chapters

def download_chapter(url, path, loop):
    base_url = "http://www.japscan.se"
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    nav = soup.find(id="pages")
    urls = []
    for elem in nav.find_all("option"):
        url = elem["value"]
        if url.startswith("/"):
            url = base_url + url
        urls.append(url)
    pages = utils.fetch_urls(urls, loop, headers=requests.headers,
                             cookies=requests.cookies)
    urls = {}
    for page in pages.values():
        soup = BeautifulSoup(page, "html.parser")
        link = soup.find(id="image")["data-src"]
        fname = link.split('/')[-1]
        if "__add" in fname.lower():
            continue # Crappy ad blocker
        urls[fname] = link
    os.makedirs(path, exist_ok=True)
    utils.download_urls(urls, path, loop, headers=requests.headers,
                        cookies=requests.cookies)
