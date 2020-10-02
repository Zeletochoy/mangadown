from . import utils
import json
import os
import requests


def get_manga_progress(user):
    url = "https://api.jikan.moe/v3/user/{}/mangalist/reading".format(user)
    res = requests.get(url)
    return {m["title"]: m["read_chapters"] for m in res.json()["mangas"]}


def get_mal_title(search):
    cache = {}
    module_path = os.path.join(os.path.dirname(__file__), "..")
    cache_path = os.path.join(module_path, "cache", "mal.json")
    if os.path.isfile(cache_path):
        with open(cache_path) as f:
            cache = json.load(f)
        if search in cache:
            return cache[search]
    url = "https://api.jikan.moe/v3/search/manga?q=" + search
    res = requests.get(url)
    choices = [m["title"] for m in res.json()["results"]]
    if len(choices) == 0:
        return None
    title = ""
    for choice in choices:
        if search.lower() == choice.lower():
            title = choice
    if title == "":
        title = utils.user_choice("Choose title for " + search, choices[:10])
    cache[search] = title
    with open(cache_path, 'w') as f:
        json.dump(cache, f)
    return title
