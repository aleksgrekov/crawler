import asyncio
import aiofiles
import aiohttp
from bs4 import BeautifulSoup
from pathlib import Path

URLS = ['https://yandex.com.am/weather?lat=55.11314392&lon=61.27467728',
        'https://yandex.com.am/weather/?lat=55.75581741&lon=37.61764526']
VISITED_URLS = set()

MAX_DEPTH = 3

file_lock = asyncio.Lock()


async def get_links(client: aiohttp.ClientSession, url: str, depth: int):
    if depth > MAX_DEPTH:
        return

    VISITED_URLS.add(url)

    try:
        async with client.get(url) as response:
            result = await response.read()
            soup = BeautifulSoup(result, "lxml")

            links = [link.get('href') for link in soup.find_all('a')
                     if link.get('href').startswith('https://')]
            if links:
                await write_to_disk(links, url)
            tasks = [get_links(client, url, depth + 1) for url in links
                     if url not in VISITED_URLS]
            await asyncio.gather(*tasks)
    except Exception as e:
        print(f"Failed to get {url}: {e}")


async def write_to_disk(links: list, url: str):
    global file_lock
    content = '\n\t'.join(links)
    file_path = '{}/{}.txt'.format(Path(__file__).parent, 'links')
    async with file_lock:
        async with aiofiles.open(file_path, mode='a') as file:
            await file.write(f"\nLinks from {url}:\n\t")
            await file.write(content)


async def get_all_links():
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(15)) as client:
        tasks = [get_links(client=client, url=url, depth=0) for url in URLS]
        await asyncio.gather(*tasks)


def main():
    asyncio.run(get_all_links())


if __name__ == '__main__':
    main()
