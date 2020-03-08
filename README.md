# prom-corona: Coronavirus Data in Prometheus Format

This repo contains scripts to convert Johns Hopkins Coronavirus data into Prometheus timeseries format. The `convert.py` script can
be used to either serve the latest datapoints (i.e. run as an exporter) or create a file suitable for use with `roidelaplui/ingest`
to backfill a Prometheus server with.

You'll need `go` to build `ingest`, and `docker` takes care of the rest. Going to move ingest into Docker at some point.

## Endpoints

This exporter, along with a backfilled Prometheus instance, can be found here:

* [Prometheus Server for Federation](https://covid.zack.gg:9000)
* [Exporter Endpoint](http://covid.zack.gg:9001)

## Exporter

The exporter is configurable with environment variables:

* `PROM_PORT`: default 8000, port to serve prometheus metrics on
* `DATA_ROOT`: default `/data`, where to find the `johns-hopkins` folder from this repo. Expects a checkout in `$DATA_ROOT/repo`
* `INTERVAL`: default 60, in seconds, how often to reload files from the data root

It runs in docker, but you can also run it elsewhere, so long as you satisfy requirements.txt. There's a make target to build
the docker image and pull in the latest upstream data. I recommend bind mounting the upstream data into the container and
updating it with a cron or similar:

```
    make docker johns-hopkins/repo
    docker run -v $(pwd)/johns-hopkins:/data -p 8000:8000 zdoherty/prom-corona
```

## Backfill

For creating a backfilled prometheus database, you'll need `roidelaplui/ingest`. There's a make target to build that, create
the input file with the latest data, and convert it into a prometheus TSDB in the `output` directory:

```
    make output
```

