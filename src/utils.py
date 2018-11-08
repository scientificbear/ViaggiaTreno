import asyncio
from aiohttp import ClientSession
import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


async def fetch(url, session, head):
    """Fetch a url, using specified ClientSession."""
    f = session.get if not head else session.head
    async with f(url, allow_redirects=False, timeout=180) as response:
        content = await response.read()
        if response.status != 200:
            logging.warning('Url {} - http status {}'.format(url, response.status))
        return dict(content=content, status_code=response.status, url=url)


async def fetch_all(pages, head=False):
    """Launch requests for all web pages."""
    tasks = []
    async with ClientSession() as session:
        for p in pages:
            task = asyncio.create_task(fetch(**dict(url=p['url'], session=session, head=head)))
            tasks.append(task) # create list of tasks
        results = await asyncio.gather(*tasks) # gather task responses
    return results


def call_urls(urls):

    logging.info("Start downloading")
    loop = asyncio.get_event_loop() # event loop
    futures = asyncio.ensure_future(fetch_all(urls)) # tasks to do
    results = loop.run_until_complete(futures) # loop until done
    logging.info("Done downloading")

    return results
