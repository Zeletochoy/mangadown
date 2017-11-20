import requests
import xml.etree.ElementTree as XML
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import json
import os
import utils
from collections import OrderedDict, defaultdict
from settings import *

def get_manga_progress(user):
    url = "https://myanimelist.net/malappinfo.php?status=all&type=manga&u="
    url += user
    page = requests.get(url)
    xml = XML.fromstring(page.text)
    progress = defaultdict(lambda: 0)
    for m in xml.findall("manga"):
        title = m.find("series_title").text
        count = int(m.find("my_read_chapters").text)
        progress[title] = count
    return progress

def get_mal_title(search):
    cache = {}
    if os.path.isfile("mal.json"):
        with open("mal.json") as f:
            cache = json.load(f)
        if search in cache:
            return cache[search]
    url = "https://myanimelist.net/manga.php?q="
    url += search
    page = requests.get(url)
    page = BeautifulSoup(page.text, "html.parser")
    choices = []
    for link in page.find_all('a', class_="hoverinfo_trigger fw-b"):
        name = link.text
        if not name in choices:
            choices.append(name)
    if len(choices) == 0:
        return None
    title = ""
    for choice in choices:
        if search.lower() == choice.lower():
            title = choice
    if title == "":
        title = utils.user_choice("Choose title for " + search, choices[:10])
    cache[search] = title
    with open("mal.json", 'w') as f:
        json.dump(cache, f)
    return title
