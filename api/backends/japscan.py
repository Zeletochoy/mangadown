#! /usr/bin/env python3

from .. import utils
import cfscrape
from bs4 import BeautifulSoup
import os
import re

requests = cfscrape.create_scraper()

@utils.json_cached("japscan.json")
def get_mangas():
    print("Fetching manga list from japscan.com")
    url = "http://www.japscan.com/mangas/"
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    tab = soup.find(id="liste_mangas")
    mangas = {}
    for manga in tab.find_all('a'):
        url = manga["href"]
        if url.startswith("/mangas"):
            title = manga.text.lower()
            mangas[title] = url
    return mangas

def get_chapters(url):
    url = "http://www.japscan.com" + url
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    tab = soup.find(id="liste_chapitres")
    chapters = {}
    for chap in tab.find_all("a"):
        url = "http:" + chap["href"]
        if "lecture-en-ligne" in url:
            match = re.search("(\d+)(?!.*\d)", url)
            num = float(match.group(1))
            chapters[num] = url
    return chapters

def download_chapter(url, path, loop):
    os.makedirs(path, exist_ok=True)
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    nav = soup.find(id="pages")
    urls = []
    for elem in nav.find_all("option"):
        url = "http://www.japscan.com" + elem["value"]
        urls.append(url)
    pages = utils.fetch_urls(urls, loop, headers=requests.headers,
                             cookies=requests.cookies)
    urls = {}
    for page in pages.values():
        soup = BeautifulSoup(page, "html.parser")
        link = soup.find(id="image")["src"]
        fname = link.split('/')[-1]
        if "__add" in fname.lower():
            continue # Crappy ad blocker
        urls[fname] = link
    utils.download_urls(urls, path, loop, headers=requests.headers,
                        cookies=requests.cookies)

if __name__ == "__main__":
    print("Fetching manga list...")
    mangas = get_mangas()
    url = mangas["berserk"]
    print("Fetching chapters for Berserk...")
    chapters = get_chapters(url)
    import asyncio
    loop = asyncio.get_event_loop()
    print("Downloading Tome 1 fo Berserk...")
    download_chapter(chapters[1.0], "berserk 1", loop)