#!/usr/bin/env python
import csv
import os
import datetime
import argparse
import json

from prometheus_client import Counter

# filenames from johns hopkins repo
STATUSES = ("Confirmed", "Deaths", "Recovered")
TIMESERIES_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'repo',
                               'csse_covid_19_data',
                               'csse_covid_19_time_series')
TIMESERIES_FN_FMT = "time_series_19-covid-{status}.csv"
TIMESERIES_FILES = {"%s_total" % s.lower(): os.path.join(TIMESERIES_ROOT, TIMESERIES_FN_FMT.format(status=s)) for s in STATUSES}

# csv header: Province/State,Country/Region,Lat,Long,1/22/20,...
DATEFMT = "%m/%d/%y"
STATEI, REGIONI, LATI, LONGI, SERIES_START = 0, 1, 2, 3, 4
US_SPECIAL = (
    'Unassigned Location (From Diamond Princess)'
)

confirmed = Counter('confirmed_total', 'Number of confirmed cases')
deaths = Counter('deaths_total', 'Number of fatalities')
recovered = Counter('recovered_total', 'Number of recovered cases')


class Locality(object):
    def __init__(self, state, region, lat, long):
        self.state = state
        self.region = region
        self.lat = lat
        self.long = long

    def as_labels(self):
        l = {
            "region": self.region,
            "lat": self.lat,
            "long": self.long,
        }
        if self.state:
            l["state"] = self.state
        if self.region == 'US' and self.state not in US_SPECIAL:
            # try to parse county in US
            split = self.state.split(", ")
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
            "__name__": name,
        }
        labels.update(self.locality.as_labels())
        oldpoints = []
        for date, point in zip(self.dates, self.points):
            oldpoints.append({
                "l": labels,
                "t": int(round(date.timestamp() * 1000)),
                "v": int(point),
            })
        return oldpoints


def parse_file(filename):
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


def backfill(data):
    metrics = []
    for metric, series in data.items():
        for s in series:
            metrics.extend(s.backfill(metric))
    return metrics


def serve(data):
    pass


def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=[
        'backfill',
        'serve'
    ], type=str, default='serve')
    args = p.parse_args()
    data = load()
    if args.action == 'backfill':
        print(json.dumps(backfill(data)))
    else:
        serve(data)

if __name__ == '__main__':
    main()
