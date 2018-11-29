import asyncio
from aiohttp import ClientSession
import os
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from random import randint
import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


async def fetch(url, session, head):
    """Fetch a url, using specified ClientSession."""
    f = session.get if not head else session.head
    try:
        async with f(url, allow_redirects=False, timeout=300) as response:
            content = await response.read()
            if response.status != 200:
                logging.warning('Url {} - http status {}'.format(url, response.status))
            else:
                logging.debug('Url {} - http status {}'.format(url, response.status))

            if randint(0,10)>8:
                await asyncio.sleep(1)
            return dict(content=content, status_code=response.status, url=url)
    except Exception:
        logging.warning("Can't fetch %s (%s)", url, Exception)
        return dict(content={}, status_code=504, url=url)


async def fetch_all(pages, head=False):
    """Launch requests for all web pages."""
    tasks = []
    # proxies = get_proxies()
    # proxies = [x for x in proxies if x['https']=='no']
    async with ClientSession() as session:
        for n, p in enumerate(pages):
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


def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def test_proxy(proxy):
    req = Request('http://www.viaggiatreno.it/viaggiatrenonew/resteasy/viaggiatreno/andamentoTreno/S00228/4640')
    req.set_proxy(proxy, 'http')
    try:
        my_ip = urlopen(req).read().decode('utf8')
        return True
    except Exception as e:
        return False



def get_proxies():

    ua = UserAgent()
    proxies = []

    # Retrieve latest proxies
    proxies_req = Request('https://free-proxy-list.net/')
    proxies_req.add_header('User-Agent', ua.random)
    proxies_doc = urlopen(proxies_req).read().decode('utf8')

    soup = BeautifulSoup(proxies_doc, 'html.parser')
    proxies_table = soup.find(id='proxylisttable')

    # Save proxies in the array
    for row in proxies_table.tbody.find_all('tr'):
        proxies.append({
            'ip':   row.find_all('td')[0].string,
            'port': row.find_all('td')[1].string,
            'https': row.find_all('td')[6].string
        })

    return proxies
