import csv
import logging
import time
from random import random
from utils import call_urls
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


def get_starting_station(train_list):

    get_starting_station_url = 'http://www.viaggiatreno.it/viaggiatrenonew/resteasy/viaggiatreno/cercaNumeroTrenoTrenoAutocomplete/{}'
    pages = [{'url': get_starting_station_url.format(n)} for n in train_list]

    starting_stations = call_urls(pages)

    starting_stations = ''.join([item['content'].decode("utf-8")
                                 for item in starting_stations
                                 if len(item['content'].decode("utf-8"))>0])
    starting_stations = starting_stations[:-1]

    return starting_stations


def main(configs):

    step = configs.get('step', 100)
    waiting_time = configs.get('waiting_time', 3)
    output_file = configs.get('output_file')

    with open(output_file, mode='w') as f:

        f_writer = csv.writer(f, delimiter=',',
                              quotechar='"',
                              quoting=csv.QUOTE_MINIMAL)
        f_writer.writerow(['train_name', 'train_number', 'starting_station'])

        for k in range(configs.get('start_from'), configs.get('up_to'), step):
            time.sleep(random()*waiting_time)
            train_list =range(k, k+step)
            logging.info("Processing chunk from %s to %s (%s items)",
                k, k+step, len(train_list))

            starting_stations = get_starting_station(train_list)

            if len(starting_stations)>0:
                logging.info("Save csv")
                for item in starting_stations.split('\n'):
                    item = item.split('|')[0] + '|' \
                        + item.split('|')[1].replace('-','|')
                    f_writer.writerow(item.split('|'))
            else:
                logging.info("Nothing to save")
            logging.info("Chunk done")

        f_writer.writerow('')


if __name__ == '__main__':
    logging.info("Start get_train_numbers.py")
    configs = {'output_file': '../data/starting_stations.csv',
               'start_from': 0,
               'up_to': 100000,
               'step': 500}
    main(configs)
    logging.info("Done get_train_numbers.py")
