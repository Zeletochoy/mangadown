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
    base_url = "http://www.japscan.com"
    url = base_url + url
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    tab = soup.find(id="liste_chapitres")
    chapters = {}
    for chap in tab.find_all("a"):
        url = base_url + chap["href"]
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
