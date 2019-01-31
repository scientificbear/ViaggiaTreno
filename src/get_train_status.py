import csv
import logging
import os
import time
from random import random
import json
from utils import call_urls, create_dir, logger, train
from tqdm import tqdm
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(funcName)s : %(message)s', level=logging.INFO)


@logger
def get_train_status_from_API(station_id_list):

    get_train_status_url = 'http://www.viaggiatreno.it/viaggiatrenonew/resteasy/viaggiatreno/andamentoTreno/{}/{}'
    logging.info("Processing %s trains/stations", len(station_id_list))
    pages = [{'url': get_train_status_url.format(item[0], item[1])}
             for item in station_id_list]

    train_status = call_urls(pages)

    train_status = [item['content'].decode("utf-8")
                    for item in train_status
                    if len(item['content'].decode("utf-8"))>0]

    logging.info("Returning from API the status of %s trains", len(train_status))
    return(train_status)


@logger
def write_to_files(train_status):

    today = time.strftime('%Y-%m-%d', time.localtime(time.time()))

    f_out_fname = '../data/train_status/{}.csv'.format(today)
    f_out_header = ['train_number', 'trip_date', 'train_type', 'category',
                    'origin_id', 'origin', 'destination_id', 'destination',
                    'num_stops', 'num_deleted_stops']
    f_stat_fname = '../data/single_train_status/{}.csv'.format(today)
    f_stat_header = ['train_number', 'trip_date', 'step',
                     'from_id', 'from_planned', 'from_real',
                     'to_id', 'to_planned', 'to_real',
                     'inc_delay', 'seg_delay', 'fin_delay']

    with open(f_out_fname, 'a') as f_out, open(f_stat_fname, 'a') as f_stat:
        logging.info("Writing to %s and %s", f_out_fname, f_stat_fname)
        writer_out = csv.DictWriter(f_out, fieldnames=f_out_header, quoting=csv.QUOTE_MINIMAL)
        writer_out.writeheader()
        writer_stat = csv.DictWriter(f_stat, fieldnames=f_stat_header, quoting=csv.QUOTE_MINIMAL)
        writer_stat.writeheader()

        for item in tqdm(train_status, disable=None, desc="Writing"):
            single_train = train(item)
            try:
                writer_out.writerow(single_train.get_train_info())
            except Exception as e:
                logging.error("writer_out" + str(e)
                    + "\ntrain {}".format(json.loads(item).get('numeroTreno')))

            try:
                for stop in single_train.parse_segments():
                    writer_stat.writerow(stop)
            except Exception as e:
                logging.error("writer_stat" + str(e)
                    + "\ntrain {}".format(json.loads(item).get('numeroTreno')))


def main():

    with open('../data/starting_stations.csv', 'r') as f:
        csv_reader = csv.DictReader(f)
        station_id_train = [(item['starting_station'], item['train_number'])
                            for item in csv_reader]
                            # if int(item['train_number']) < 34]
        # TO DO: what about duplicated ids?

    logging.info("station_id_train: %s items", len(station_id_train))

    create_dir('../data/train_status')
    create_dir('../data/single_train_status')

    train_status = []
    chunk_size = 100
    for k in tqdm(range(0, len(station_id_train), chunk_size)):
        try:
            raw = get_train_status_from_API(station_id_train[k:(k+chunk_size)])
            train_status.extend(raw)
        except:
            logging.warning("Sleeping")
            time.sleep(10)

    logging.info("train_status %s", len(train_status))

    write_to_files(train_status)


if __name__ == '__main__':
    logging.info('Start get_train_status.py')
    main()
    logging.info('Done get_train_status.py')
