import aiohttp
import asyncio
import os
import socket
import json


async def _download(session, url, path, headers):
    async with session.get(url, headers=headers) as response:
        with open(path, "wb") as f:
            f.write(await response.read())

async def _download_all(urls, path, loop, headers, cookies):
    conn = aiohttp.TCPConnector(family=socket.AF_INET, verify_ssl=False)
    async with aiohttp.ClientSession(connector=conn, loop=loop, cookies=cookies) as session:
        tasks = []
        for fname, url in urls.items():
            fullpath = os.path.join(path, fname)
            task = loop.create_task(_download(session, url, fullpath, headers))
            tasks.append(task)
        await asyncio.gather(*tasks)

# urls: {filename: url}
# path: destination directory (already created)
# loop: asyncio loop
def download_urls(urls, path, loop, headers={}, cookies={}):
    loop.run_until_complete(_download_all(urls, path, loop, headers, cookies))


async def _fetch(session, url, res, headers):
    async with session.get(url, headers=headers) as response:
        res[url] = await response.text()

async def _fetch_all(urls, res, loop, headers, cookies):
    conn = aiohttp.TCPConnector(family=socket.AF_INET, verify_ssl=False)
    async with aiohttp.ClientSession(connector=conn, loop=loop, cookies=cookies) as session:
        await asyncio.gather(*[loop.create_task(_fetch(session, url, res, headers)) for url in urls])

# urls: [url]
# loop: asyncio loop
# return: {url: page}
def fetch_urls(urls, loop, headers={}, cookies={}):
    res = {}
    loop.run_until_complete(_fetch_all(urls, res, loop, headers, cookies))
    return res


def user_choice(prompt, choices):
    print(prompt)
    for i, c in enumerate(choices):
        print("[{}] {}".format(i, c))
    res = choices[0]
    while True:
        n = input("Choice: ")
        if n == "":
            break
        try:
            n = int(n)
        except:
            print("Invalid input")
            continue
        if n >= len(choices):
            print("Out of range")
            continue
        res = choices[n]
        break
    return res

def json_cached(path):
    module_path = os.path.join(os.path.dirname(__file__), "..")
    folder = os.path.join(module_path, "cache")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, path)
    def decorator(func):
        def wrapped(*args, **kwargs):
            if os.path.isfile(path):
                cache = {}
                with open(path) as f:
                    cache = json.load(f)
                return cache
            res = func(*args, **kwargs)
            with open(path, "w") as f:
                json.dump(res, f)
            return res
        return wrapped
    return decorator
