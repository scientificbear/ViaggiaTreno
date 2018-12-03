import json
from utils import call_urls
import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)



def get_stations():
    get_station_url = 'http://www.viaggiatreno.it/viaggiatrenonew/resteasy/viaggiatreno/cercaStazione/{}'
    pages = [{'url': get_station_url.format(l)}
             for l in 'ABCDEFGHILMNOPQRSTUV']
    stations = call_urls(pages)
    stations = [json.loads(item['content'].decode("utf-8"))
                        for item in stations
                        if len(item['content'].decode("utf-8"))>0]
    result = {}
    for item in stations:
        for subitem in item:
            result[subitem['id']]=subitem
    return result


def get_region(stations):
    get_region_url = 'http://www.viaggiatreno.it/viaggiatrenonew/resteasy/viaggiatreno/regione/{}'
    pages = [{'url': get_region_url.format(stations[s]['id'])}
             for s in stations]
    logging.info("Going to make %s requests", len(pages))
    regions = call_urls(pages)
    for item in regions:
        if len(item['content'].decode("utf-8"))>0:
            stations[item['url'].split('/')[-1]]['region'] = item['content'].decode("utf-8")
    return stations


def get_coordinates(stations):
    get_coord_url = 'http://www.viaggiatreno.it/viaggiatrenonew/resteasy/viaggiatreno/dettaglioStazione/{}/{}'
    pages = [{'url': get_coord_url.format(stations[s]['id'], stations[s]['region'])}
             for s in stations
             if stations[s].get('region') is not None]
    logging.info("Going to make %s requests", len(pages))
    coords = call_urls(pages)
    for item in coords:
        if len(item['content'].decode("utf-8"))>0:
            stations[item['url'].split('/')[-2]].update(json.loads(item['content'].decode("utf-8")))
    return stations


def get_position(stations, more=''):
    get_coord_url = 'http://www.datasciencetoolkit.org/maps/api/geocode/json?address={}' + more + '&?id{}'
    pages = [{'url': get_coord_url.format(stations[s]['nomeLungo'], stations[s]['id'])}
             for s in stations
             if stations[s].get('lat') is None]
    logging.info("Going to make %s requests", len(pages))
    position = call_urls(pages)
    for item in position:
        content = json.loads(item['content'].decode("utf-8"))
        if len(content)>0 and content['status']=='OK':
            id = item['url'].split('?')[-1].replace('id','')
            stations[id]['lon'] = content['results'][0]['geometry']['location']['lng']
            stations[id]['lat'] = content['results'][0]['geometry']['location']['lat']
    return stations


def main():
    stations_raw = get_stations()
    stations = get_region(stations)
    stations = get_coordinates(stations)
    stations = get_position(stations, more='')
    stations = get_position(stations, more=' ITALIA')

    with open('../data/stations.json', 'w') as f:
        json.dump(stations, f, ensure_ascii=False)

    with open('../data/stations.csv', 'w') as f:
        f.write('id,nomeLungo,nomeBreve,lon,lat,region,codRegion,tipoStazione\n')
        for key, value in stations_ext.items():
            f.write('{},"{}","{}",{},{},{},{},{}\n'.format(
                value.get('id'),
                value.get('nomeLungo'),
                value.get('nomeBreve'),
                value.get('lon'),
                value.get('lat'),
                value.get('region'),
                value.get('codRegion'),
                value.get('tipoStazione')
            ))

if __name__ == '__main__':
    main()
