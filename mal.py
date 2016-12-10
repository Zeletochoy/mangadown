import requests
import xml.etree.ElementTree as XML
from urllib.parse import quote_plus
import json
import os
import utils
from settings import *

def get_manga_progress(user):
    url = "https://myanimelist.net/malappinfo.php?status=all&type=manga&u="
    url += user
    page = requests.get(url)
    xml = XML.fromstring(page.text)
    progress = {}
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
    url = "https://myanimelist.net/api/manga/search.xml?q="
    url += quote_plus(search)
    creds = (MAL_USER, MAL_PASS)
    page = requests.get(url, auth=creds)
    xml = XML.fromstring(page.text)
    choices = xml.findall("entry/title")
    if len(choices) == 0:
        return None
    choices = [t.text for t in choices]
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
