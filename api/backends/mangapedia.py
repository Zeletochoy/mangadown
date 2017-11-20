from .. import utils
import re
import os
import io
import zipfile
import cfscrape
from bs4 import BeautifulSoup

requests = cfscrape.create_scraper()

@utils.json_cached("mangapedia.json")
def get_mangas():
    print("Fetching manga list from mangapedia")
    url = "http://mangapedia.fr/project_code/script/moreMangas.php"
    params = {"pageNumber": 1}
    mangas = {}
    while True:
        print("Fetching page {}...".format(params["pageNumber"]))
        page = requests.post(url, data=params)
        soup = BeautifulSoup(page.text, "html.parser")
        count = 0
        for a in soup.find_all('a'):
            try:
                code = a["href"].split('/')[-1]
                name = a.find("div").string.lower()
                mangas[name] = code
                count += 1
            except:
                continue
        if count == 0:
            break
        params["pageNumber"] += 1
    return mangas

def get_chapters(manga):
    url = "http://mangapedia.fr/manga/" + manga
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    chapters = {}
    for a in soup.find_all('a'):
        if a["href"].startswith("http://mangapedia.fr/lel/"):
            link = a["href"]
            # Some chapters have dots...
            try:
                chap_nb = link.split('/')[-2]
                n = float(chap_nb)
                chapters[n] = link
            except:
                print("Unable to parse chapter number: {}".format(chap_nb))
                continue
    return chapters

def download_chapter_pages(page, path, loop):
    links = next(l for l in page.text.split('\n') if "var arrImageData =" in l)
    links = links.strip()[len("var arrImageData = "):]
    links = [l for l in links.split('"') if l.startswith("http")]
    urls = {}
    for l in links:
        match = re.search("&FileName=(.*)&", l)
        fname = match.group(1)
        if "__add" in fname.lower():
            continue # Crappy ad blocker
        urls[fname] = l
    headers = {"Referer": page.url}
    utils.download_urls(urls, path, loop, headers)

def download_chapter_zip(page, path):
    soup = BeautifulSoup(page.text, "html.parser")
    clictune = soup.find(id="downloadChapterConfirm")
    if clictune is None:
        return False
    clictune = clictune.parent["href"]
    headers = {"Referer": page.url}
    clictune = requests.get(clictune, headers=headers)
    link = ""
    for l in clictune.text.split('"'):
        if "http://www.clictune.com/redirect.php" in l:
            link = l
    headers = {"Referer": clictune}
    data = requests.get(link, headers=headers).content
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(path)
    return True

def download_chapter(url, path, loop):
    os.makedirs(path, exist_ok=True)
    page = requests.get(url)
    #if not download_chapter_zip(page, path):
    download_chapter_pages(page, path, loop)
