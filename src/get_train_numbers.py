import string
import asyncio
from aiohttp import ClientSession
import pickle
import csv
from tqdm import tqdm
import json
import logging
import time
from random import random
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


def get_starting_station(train_list):

    get_starting_station_url = 'http://www.viaggiatreno.it/viaggiatrenonew/resteasy/viaggiatreno/cercaNumeroTrenoTrenoAutocomplete/{}'
    pages = [{'url': get_starting_station_url.format(n)} for n in train_list]

    loop = asyncio.get_event_loop() # event loop
    futures = asyncio.ensure_future(fetch_all(pages)) # tasks to do
    starting_stations = loop.run_until_complete(futures) # loop until done
    logging.info("Done downloading")

    starting_stations = ''.join([item['content'].decode("utf-8")
                                 for item in starting_stations
                                 if len(item['content'].decode("utf-8"))>0])
    starting_stations = starting_stations[:-1]

    return starting_stations


def main(output_file):
    with open(output_file, mode='w') as f:

        f_writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        f_writer.writerow(['train_name', 'train_number', 'starting_station'])

        for k in range(0, 1000000, 500):
            time.sleep(random()*3)
            train_list =range(k, k+500)
            logging.info("Processing chunk from %s to %s (%s items)", k, k+500, len(pages))

            starting_stations = get_starting_station(train_list)

            if len(starting_stations)>0:
                logging.info("Save csv")
                for item in starting_stations.split('\n'):
                    item = item.split('|')[0] + '|' + item.split('|')[1].replace('-','|')
                    f_writer.writerow(item.split('|'))
            else:
                logging.info("Nothing to save")
            logging.info("Chunk done")

        f_writer.writerow('')


if __name__ == '__main__':
    logging.info("Start get_train_numbers.py")
    main(output_file='../data/starting_stations.csv')
    logging.info("Done get_train_numbers.py")
