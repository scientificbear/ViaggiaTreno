import asyncio
from aiohttp import ClientSession
import os
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from random import randint
import logging
import json
import time

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(funcName)s : %(message)s', level=logging.INFO)


def logger(fn):
    from functools import wraps
    import inspect
    @wraps(fn)
    def wrapper(*args, **kwargs):
        log = logging.getLogger(fn.__name__)
        log.info('About to run %s' % fn.__name__)

        start_time = time.time()
        out = fn(*args, **kwargs)

        log.info('Done running %s (%s s)', fn.__name__, round(time.time()-start_time,2))
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


def create_dir(path):
    if not os.path.exists(path):
        logging.info("Creating dir %s", path)
        os.makedirs(path)


class train:

    def __init__(self, raw):

        logging.debug("Initialising train with raw: %s...", raw[:10])
        self.raw = json.loads(raw)

        self.train_number = self.raw.get('numeroTreno', '')
        self.train_type = self.raw.get('tipoTreno', '')
        self.category = self.raw.get('categoria','')
        self.trip_date = time.strftime('%Y-%m-%d', time.localtime(time.time())) # self.raw.get('orarioPartenzaZero')
        # if self.trip_date is None:
        #     self.trip_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        # else:
        #     self.trip_date = time.strftime('%Y-%m-%d', time.localtime(self.trip_date/1000))
        self.provision = self.raw.get('provvedimento', '')
        self.deleted_stops = self.raw.get('fermateSoppresse', [])
        if self.deleted_stops is None:
            self.deleted_stops = []
        self.origin = self.raw.get('origine', self.raw.get('origineEstera', None))
        self.origin_id = self.raw.get('idOrigine', -1)
        self.destination = self.raw.get('destinazione', self.raw.get('destinazioneEstera', None))
        self.destination_id = self.raw.get('idDestinazione')
        self.stops = self.raw.get('fermate', [])

        if self.train_type in ('PP', 'SI', 'SF', 'ST') or self.provision==1:
            logging.warning('The train %s has been deleted', self.train_number)
        if self.raw.get('haCambiNumero',False) is not False or self.raw.get('riprogrammazione', None) is not None:
            logging.warning('The train %s has changed id', self.train_number)

        logging.debug("Initialisation compleated")

    def __len__(self):
        logging.debug("Returning number of stops")
        return len(self.stops)

    def __str__(self):
        return json.dumps(self.raw)



    def get_train_info(self):
        logging.debug("Returning train info as dict")
        return  {'train_number': self.train_number,
                 'trip_date': self.trip_date,
                 'train_type': self.train_type,
                 'category': self.category,
                 'origin_id': self.origin_id,
                 'origin': self.origin,
                 'destination_id': self.destination_id,
                 'destination': self.destination,
                 'num_stops': len(self.stops),
                 'num_deleted_stops': len(self.deleted_stops)}

    def parse_segments(self):

        logging.debug("Parsing segments")

        def get_single_delay(start_pl, start_real, end_pl, end_real, step_n, train_n = self.train_number):

            logging.debug("(%s, %s), (%s, %s) for train %s - %s",
                          start_pl, start_real, end_pl, end_real, train_n, step_n)
            incoming_delay = None
            segment_delay = None
            final_delay = None
            try:
                if (start_pl is None or start_real is None)\
                        and not (end_pl is None or end_real is None):
                    logging.debug("start_* not available for train %s - %s", train_n, step_n)
                    final_delay = int((end_real - end_pl)/1000)

                elif not (start_pl is None or start_real is None)\
                        and (end_pl is None or end_real is None):
                    logging.debug("end_* not available for train %s - %s", train_n, step_n)
                    incoming_delay = int((start_real - start_pl)/1000)

                elif (start_pl is None or start_real is None)\
                        and (end_pl is None or end_real is None):
                    logging.warning("start_* and end_* not available for train %s - %s", train_n, step_n)

                else:
                    incoming_delay = int((start_real - start_pl)/1000)
                    final_delay = int((end_real - end_pl)/1000)
                    segment_delay = int(final_delay - incoming_delay)

                return incoming_delay, segment_delay, final_delay

            except Exception as e:
                logging.error(str(e) + " {} - {}".format(train_n, step_n))
                return None, None, None

        def get_timestamp(dict, field):
            if dict.get(field, None) is not None:
                return dict.get(field)/1000
            else:
                return None

        step = 0
        output = []
        cum_delay = 0

        if len(self.stops) == 0:
            logger.warning("No stops for train %s", self.train_number)
            return []

        for stop_number in range(len(self.stops)-1):
            from_station = self.stops[stop_number]
            to_station = self.stops[stop_number+1]

            # from station to station itself
            inc_delay, seg_delay, fin_delay = get_single_delay(from_station.get('arrivo_teorico'),
                                                               from_station.get('arrivoReale'),
                                                               from_station.get('partenza_teorica'),
                                                               from_station.get('partenzaReale'),
                                                               step)
            output.append({'train_number': self.train_number,
                           'trip_date': self.trip_date,
                           'step': step,
                           'from_id': from_station.get('id', ''),
                           'from_planned': get_timestamp(from_station, 'arrivo_teorico'),
                           'from_real': get_timestamp(from_station, 'arrivoReale'),
                           'to_id': from_station.get('id'),
                           'to_planned': get_timestamp(from_station, 'partenza_teorica'),
                           'to_real': get_timestamp(from_station, 'partenzaReale'),
                           'inc_delay': inc_delay,
                           'seg_delay': seg_delay,
                           'fin_delay': fin_delay})
            step += 1

            inc_delay, seg_delay, fin_delay = get_single_delay(from_station.get('partenza_teorica'),
                                                               from_station.get('partenzaReale'),
                                                               to_station.get('arrivo_teorico'),
                                                               to_station.get('arrivoReale'),
                                                               step)
            output.append({'train_number': self.train_number,
                           'trip_date': self.trip_date,
                           'step': step,
                           'from_id': from_station.get('id', ''),
                           'from_planned': get_timestamp(from_station, 'partenza_teorica'),
                           'from_real': get_timestamp(from_station, 'partenzaReale'),
                           'to_id': to_station.get('id'),
                           'to_planned': get_timestamp(to_station, 'arrivo_teorico'),
                           'to_real': get_timestamp(to_station, 'arrivoReale'),
                           'inc_delay': inc_delay,
                           'seg_delay': seg_delay,
                           'fin_delay': fin_delay})
            step += 1

        logging.debug("Returning list of %s dictionaries", len(output))
        return output


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
