from .. import utils
import os
import io
import zipfile
import requests
from bs4 import BeautifulSoup

@utils.json_cached("scantradfr.json")
def get_mangas():
    print("Fetching manga list from scantrad.fr")
    url = "https://scantrad.fr/mangas"
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    mangas = {}
    for name_tag in soup.find_all("span", class_="project-name"):
        name = name_tag.string.lower()
        code = name_tag.parent["href"].split('/')[-1]
        mangas[name] = code
    return mangas

def get_chapters(manga):
    url = "http://scantrad.fr/" + manga
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    chapters = {}
    ul = soup.find(id="project-chapters-list")
    for li in ul.find_all("li"):
        nb = li.find("span", class_="chapter-number").text
        nb = float(nb.replace('#', ''))
        chapters[nb] = "https://scantrad.fr/download/{}/{}".format(manga, nb)
    return chapters

def download_chapter(url, path, loop):
    os.makedirs(path, exist_ok=True)
    data = requests.get(url).content
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(path)
