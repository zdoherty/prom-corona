# prom-corona

scripts to convert johns-hopkins covid-19 data to prometheus timeseries format

you need go and docker installed to run this

## convert and serve

```
    make docker johns-hopkins/repo
    docker run -v $(pwd)/johns-hopkins:/data -p 8000:8000 zdoherty/prom-corona
```

## generate backfilled data


```
    make output
```
