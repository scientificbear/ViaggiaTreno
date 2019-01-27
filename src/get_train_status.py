import csv
import logging
import os
import time
from random import random
import json
from utils import call_urls, create_dir
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


def get_timestamp(dict, field):
    if dict.get(field, None) is not None:
        return dict.get(field)/1000
    else:
        return None


def get_train_summary_info(data):

    train_number = data.get('numeroTreno', '')
    logging.debug('get_train_summary_info of train %s', train_number)
    train_type = data.get('tipoTreno', '')
    category = data.get('categoria','')
    trip_date = data.get('orarioPartenzaZero',0)
    if trip_date is None:
        trip_date = ''
    else:
        trip_date = time.strftime('%Y-%m-%d', time.localtime(trip_date/1000))
    provision = data.get('provvedimento', '')
    deleted_stops = data.get('fermateSoppresse', [])
    if deleted_stops is None:
        deleted_stops = []
    origin = data.get('origine', data.get('origineEstera', None))
    origin_id = data.get('idOrigine', -1)
    destination = data.get('destinazione', data.get('destinazioneEstera', None))
    destination_id = data.get('idDestinazione')
    stops = data.get('fermate', [])

    if train_type in ('PP', 'SI', 'SF', 'ST') or provision==1:
        logging.warning('The train %s has been deleted', train_number)
    if data.get('haCambiNumero',False) is not False or data.get('riprogrammazione', None) is not None:
        logging.warning('The train %s has changed id', train_number)

    train_info = [train_number,
                  trip_date,
                  train_type,
                  category,
                  origin_id,origin,
                  destination_id, destination,
                  len(stops),
                  len(deleted_stops)]
    return train_info


def get_single_delay(origin, destination):
    try:
        if (origin.get('partenzaReale') is None or
                origin.get('partenza_teorica') is None) and not (
                destination.get('arrivoReale') is None or
                destination.get('arrivo_teorico') is None):
            logging.debug('partenzaReale or partenza_teorica not available')
            incoming_delay = (destination.get('arrivoReale') - destination.get('arrivo_teorico'))/1000
            final_delay = incoming_delay
            return round(incoming_delay), 0, round(final_delay)
        elif not (origin.get('partenzaReale') is None or
                origin.get('partenza_teorica') is None) and (
                destination.get('arrivoReale') is None or
                destination.get('arrivo_teorico') is None):
            logging.debug('arrivoReale or arrivo_teorico not available')
            incoming_delay = 0
            final_delay = (origin.get('partenzaReale')-origin.get('partenza_teorica'))/1000
            segment_delay = final_delay - incoming_delay
            return round(incoming_delay), round(segment_delay), round(final_delay)
        elif (origin.get('partenzaReale') is None or
                origin.get('partenza_teorica') is None) and (
                destination.get('arrivoReale') is None or
                destination.get('arrivo_teorico') is None):
            logging.warning('Nor partenza nor arrivo are available')
            return None, None, None
        else:
            incoming_delay = (origin.get('partenzaReale')-origin.get('partenza_teorica'))/1000
            final_delay = (destination.get('arrivoReale') - destination.get('arrivo_teorico'))/1000
            segment_delay = final_delay - incoming_delay
            return round(incoming_delay), round(final_delay), round(segment_delay)
    except Exception as e:
        logging.error(e)
        return None, None, None


def get_route_info(data):

    train_number = data.get('numeroTreno', '')
    logging.info('get_route_info of train %s', train_number)

    trip_date = data.get('orarioPartenzaZero',0)
    if trip_date is None:
        trip_date = ''
    else:
        trip_date = time.strftime('%Y-%m-%d', time.localtime(trip_date/1000))
    stops = data.get('fermate', [])

    step = 0
    output = []
    ritardo_accumulato = 0
    logging.debug("Train %s has %s stops", train_number, len(stops))
    for stop_number in range(len(stops)-1):
        from_station = stops[stop_number]
        to_station = stops[stop_number+1]

        # from station to station itself
        incoming_delay, final_delay, segment_delay = get_single_delay(from_station, from_station)
        output.append([train_number,
                       trip_date,
                       step,
                       from_station.get('id', ''),
                       get_timestamp(from_station, 'arrivo_teorico'),
                       get_timestamp(from_station, 'arrivoReale'),
                       from_station.get('id'),
                       get_timestamp(from_station, 'partenza_teorica'),
                       get_timestamp(from_station, 'partenzaReale'),
                       incoming_delay,
                       segment_delay,
                       final_delay])
        step += 1

        # from station to next station
        incoming_delay, final_delay, segment_delay = get_single_delay(from_station, to_station)

        output.append([train_number,
                       trip_date,
                       step,
                       from_station.get('id', ''),
                       get_timestamp(from_station, 'partenza_teorica'),
                       get_timestamp(from_station, 'partenzaReale'),
                       to_station.get('id'),
                       get_timestamp(to_station, 'arrivo_teorico'),
                       get_timestamp(to_station, 'arrivoReale'),
                       incoming_delay,
                       segment_delay,
                       final_delay])
        step += 1

    return output


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


def write_single_train(single_train, f_out_writer, f_stat_writer):
    try:
        data = json.loads(single_train)

        train_info = get_train_summary_info(data)
        f_out_writer.writerow(train_info)

        stops = data.get('fermate', [])
        if stops is None:
            stops = []
        if len(stops) > 0:
            route_info = get_route_info(data)
            for k in route_info:
                f_stat_writer.writerow(k)
    except Exception as e:
        logging.error(e)
        create_dir('../data/errors')
        with open('../data/errors/get_train_status.csv', 'a') as f_err:
            f_err.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())) + ',' +
                        str(data.get('numeroTreno', '')) + ',' +
                        str(data.get('idOrigine', -1)) + '\n')

def main():

    with open('../data/starting_stations.csv', 'r') as f:
        csv_reader = csv.DictReader(f)
        station_id_train = [(item['starting_station'], item['train_number'])
                            for item in csv_reader]
        # for row in csv_reader:
        #     print('Train: {}\nnumber: {}\nstarting station id: {}\n'\
        #         .format(row['train_name'],
        #                 row['train_number'],
        #                 row['starting_station']))
        #
        # TO DO: what about duplicated ids?

    create_dir('../data/train_status')
    create_dir('../data/single_train_status')

    train_status = []
    for k in range(0, len(station_id_train), 100):
        try:
            raw = get_train_status_from_API(station_id_train[k:(k+100)])
            train_status.extend(raw)
        except:
            logging.warning("Sleeping")
            time.sleep(10)
    today = time.strftime('%Y-%m-%d', time.localtime(time.time()))

    with open('../data/train_status/{}.csv'.format(today), 'a') as f_out:

        f_out_writer = csv.writer(f_out, delimiter=',',
                                  quotechar='"',
                                  quoting=csv.QUOTE_MINIMAL)
        if os.stat('../data/train_status/{}.csv'.format(today)).st_size == 0:
            f_out_writer.writerow(['train_number',
                                   'trip_date',
                                   'train_type',
                                   'category',
                                   'origin_id', 'origin',
                                   'destination_id', 'destination',
                                   'num_stops',
                                   'num_deleted_stops'])
        with open('../data/single_train_status/{}.csv'.format(today), 'a') as f_stat:
            f_stat_writer = csv.writer(f_stat, delimiter=',',
                                      quotechar='"',
                                      quoting=csv.QUOTE_MINIMAL)
            if os.stat('../data/single_train_status/{}.csv'.format(today)).st_size == 0:
                f_stat_writer.writerow(
                    ['train_number',
                     'trip_date',
                     'step',
                     'from_id',
                     'from_planned_ts',
                     'from_real_ts',
                     'to_id',
                     'to_planned_ts',
                     'to_real_ts',
                     'incoming_delay',
                     'segment_delay',
                     'final_delay'])
            for single_train in train_status:
                write_single_train(single_train, f_out_writer, f_stat_writer)


if __name__ == '__main__':
    logging.info('Start get_train_status.py')
    main()
    logging.info('Done get_train_status.py')
