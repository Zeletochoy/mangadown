from .. import utils
import requests
from bs4 import BeautifulSoup
import os

@utils.json_cached("lirescan.json")
def get_mangas():
    print("Fetching manga list from lirescan.net")
    url = "http://www.lirescan.net/nanatsu-no-taizai-lecture-en-ligne/"
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    dropdown = soup.find(id="mangas")
    mangas = {}
    for manga in dropdown.find_all("option"):
        title = manga.text.lower()
        url = manga["value"]
        mangas[title] = url
    return mangas

def get_chapters(url):
    url = "http://www.lirescan.net" + url
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    dropdown = soup.find(id="chapitres")
    chapters = {}
    for chap in dropdown.find_all("option"):
        num = float(chap.text)
        url = chap["value"]
        chapters[num] = url
    return chapters

def download_chapter(url, path, loop):
    url = "http://www.lirescan.net" + url
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    nav = soup.find(class_="pagination")
    urls = []
    for elem in nav.find_all("a"):
        if elem.text.strip().isdigit():
            url = "http://www.lirescan.net" + elem["href"]
            urls.append(url)
    pages = utils.fetch_urls(urls, loop)
    urls = {}
    for page in pages.values():
        soup = BeautifulSoup(page, "html.parser")
        link = soup.find(id="image_scan")["src"]
        fname = link.split('/')[-1]
        if "__add" in fname.lower():
            continue # Crappy ad blocker
        urls[fname] = "http://www.lirescan.net" + link
    os.makedirs(path, exist_ok=True)
    utils.download_urls(urls, path, loop)
