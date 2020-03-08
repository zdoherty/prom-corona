#!/usr/bin/env python
import csv
import os
import datetime
import argparse
import json
import time
import logging
import re

from prometheus_client import Gauge, start_http_server

# configurables
PROM_PORT = int(os.environ.get('PROM_PORT', 8000))
DATA_ROOT = os.environ.get('DATA_ROOT', '/data')
DEBUG = os.environ.get('DEBUG', False)
INTERVAL = int(os.environ.get('INTERVAL', 60))

# filenames from johns hopkins repo
STATUSES = ('Confirmed', 'Deaths', 'Recovered')
TIMESERIES_ROOT = os.path.join(DATA_ROOT, 'repo', 'csse_covid_19_data', 'csse_covid_19_time_series')
TIMESERIES_FN_FMT = 'time_series_19-covid-{status}.csv'
TIMESERIES_FILES = {'%s_total' % s.lower(): os.path.join(TIMESERIES_ROOT, TIMESERIES_FN_FMT.format(status=s)) for s in STATUSES}
LABELS=['lat', 'long', 'region', 'state', 'county']
GAUGES = {
    '%s_total' % s.lower(): Gauge('%s_total' % s.lower(), 'Number of %s' % s, LABELS) for s in STATUSES
}

# csv header: Province/State,Country/Region,Lat,Long,1/22/20,...
DATEFMT = '%m/%d/%y'
STATEI, REGIONI, LATI, LONGI, SERIES_START = 0, 1, 2, 3, 4
US_SPECIAL = {'Unassigned Location (From Diamond Princess)'}

class Locality(object):
    def __init__(self, state, region, lat, long):
        if 'Diamond Princess' in state and ',' in state:
            state = re.sub(r' \(From Diamond Princess\)', '', state)
        self.state = state.strip()
        self.region = region.strip()
        self.lat = lat
        self.long = long

    def as_labels(self):
        l = {
            'region': self.region,
            'lat': self.lat,
            'long': self.long,
            'state': self.state,
            'county': '',
        }
        if self.region == 'US' and self.state not in US_SPECIAL:
            # try to parse county in US
            split = self.state.split(', ')
            l['county'], l['state'] = split[0], split[1]
        return l


class Series(object):
    def __init__(self, locality, dates, points):
        self.locality = locality
        self.points_by_date = dict(zip(dates, points))
        self.points = points
        self.dates = dates

    @property
    def latest(self):
        return self.points[-1]

    def backfill(self, name):
        # need to make a list of dicts, each dict has keys:
        # l: labels, including __name__
        # t: time, epoch millis
        # v: value
        labels = {
            '__name__': name,
        }
        labels.update(self.locality.as_labels())
        oldpoints = []
        for date, point in zip(self.dates, self.points):
            oldpoints.append({
                'l': labels,
                't': int(round(date.timestamp() * 1000)),
                'v': int(point),
            })
        return oldpoints


def parse_file(filename):
    'parse a single timeseries file'

    # header row contains labels and dates, each following row contains label values and series
    with open(filename, 'r') as infd:
        reader = csv.reader(infd)
        header = next(reader)
        rows = list(reader)

    dates = [datetime.datetime.strptime(d, DATEFMT) for d in header[SERIES_START:]]
    parsed = []
    # each row is a locality followed by a timeseries
    for row in rows:
        l = Locality(row[STATEI], row[REGIONI], row[LATI], row[LONGI])
        s = Series(l, dates, [0 if not s else s for s in row[SERIES_START:]])
        parsed.append(s)
    return parsed


def load():
    data = {}
    for series, path in TIMESERIES_FILES.items():
        data[series] = parse_file(path)
    return data


def backfill():
    'dumps data in json format expected by prom ingest'

    data = load()
    metrics = []
    for metric, serieses in data.items():
        for series in serieses:
            metrics.extend(series.backfill(metric))
    # ingest expects metrics to be sorted by time
    metrics = sorted(metrics, key=lambda x: x['t'])
    return metrics


def serve():
    'runs prometheus metric server with latest data'

    start_http_server(8000)
    while True:
        logging.info('loading data')
        data = load()
        for metric, serieses in data.items():
            for series in serieses:
                logging.debug('updating %s for labels %s', metric, series.locality.as_labels())
                GAUGES[metric].labels(**series.locality.as_labels()).set(series.latest)
        time.sleep(INTERVAL)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=[
        'backfill',
        'serve'
    ], type=str, default='serve')
    args = p.parse_args()
    logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)
    if args.action == 'backfill':
        with open(os.path.join(DATA_ROOT, 'backfill.json'), 'w') as outfd:
            json.dump(backfill(), outfd, indent=2)
    elif args.action == 'serve':
        serve()

if __name__ == '__main__':
    main()
