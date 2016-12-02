import aiohttp
import asyncio
import os

async def _fetch(session, url, path, headers):
    async with session.get(url, headers=headers) as response:
        with open(path, "wb") as f:
            f.write(await response.read())

async def _fetch_all(session, urls, path, loop, headers):
    tasks = []
    for fname, url in urls.items():
        fullpath = os.path.join(path, fname)
        task = loop.create_task(_fetch(session, url, fullpath, headers))
        tasks.append(task)
    await asyncio.wait(tasks)

# urls: {filename: url}
# path: destination directory (already created)
# loop: asyncio loop
def download_urls(urls, path, loop, headers={}):
    with aiohttp.ClientSession(loop=loop) as session:
        loop.run_until_complete(
                _fetch_all(session, urls, path, loop, headers))

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

