import asyncio
from aiohttp import ClientSession
import os
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from random import randint
import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(funcName)s : %(message)s', level=logging.INFO)


def logger(fn):
    from functools import wraps
    import inspect
    @wraps(fn)
    def wrapper(*args, **kwargs):
        log = logging.getLogger(fn.__name__)
        log.info('About to run %s' % fn.__name__)

        out = fn(*args, **kwargs)

        log.info('Done running %s' % fn.__name__)
        # Return the return value
        return out
    return wrapper


async def fetch_single(url, session):
    async with session.get(url, allow_redirects=False, timeout=300) as response:
        content = await response.read()
        if response.status != 200:
            logging.warning('Url {} - http status {}'.format(url, response.status))
        else:
            logging.debug('Url {} - http status {}'.format(url, response.status))
        if randint(0,10)>8:
            await asyncio.sleep(1)
        return dict(content=content, status_code=response.status, url=url)


@logger
async def fetch_urls(urls):
    tasks = []
    # Fetch all responses within one Client session,
    # keep connection alive for all requests.
    async with ClientSession() as session:
        for url in urls:
            task = asyncio.ensure_future(fetch_single(url['url'], session))
            tasks.append(task)
        responses = await asyncio.gather(*tasks)
        # you now have all response bodies in this variable
        return responses


@logger
def call_urls(urls):
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(fetch_urls(urls))
    results = loop.run_until_complete(future)

    return results


@logger
def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


# def test_proxy(proxy):
#     req = Request('http://www.viaggiatreno.it/viaggiatrenonew/resteasy/viaggiatreno/andamentoTreno/S00228/4640')
#     req.set_proxy(proxy, 'http')
#     try:
#         my_ip = urlopen(req).read().decode('utf8')
#         return True
#     except Exception as e:
#         return False
#
#
#
# def get_proxies():
#
#     ua = UserAgent()
#     proxies = []
#
#     # Retrieve latest proxies
#     proxies_req = Request('https://free-proxy-list.net/')
#     proxies_req.add_header('User-Agent', ua.random)
#     proxies_doc = urlopen(proxies_req).read().decode('utf8')
#
#     soup = BeautifulSoup(proxies_doc, 'html.parser')
#     proxies_table = soup.find(id='proxylisttable')
#
#     # Save proxies in the array
#     for row in proxies_table.tbody.find_all('tr'):
#         proxies.append({
#             'ip':   row.find_all('td')[0].string,
#             'port': row.find_all('td')[1].string,
#             'https': row.find_all('td')[6].string
#         })
#
#     return proxies
