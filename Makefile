docker:
	docker build -t zdoherty/prom-corona:latest .

# ingest - tool for backfill prometheus data
ingest-repo:
	git clone https://github.com/roidelapluie/ingest ingest-repo
ingest: ingest-repo
	cd ingest-repo && go build -o ../ingest

# johns hopkins covid19 data
johns-hopkins/repo:
	git clone https://github.com/CSSEGISandData/COVID-19 johns-hopkins/repo

# input for ingest from jh repo
johns-hopkins/backfill.json: johns-hopkins/repo docker
	docker run -v $(shell pwd)/johns-hopkins:/data zdoherty/prom-corona backfill

output: ingest johns-hopkins/backfill.json
	./ingest -input-file=johns-hopkins/backfill.json
	chmod -R 777 output

clean-jh:
	@-rm -rf johns-hopkins/repo

clean-backfill:
	@-rm -f johns-hopkins/backfill.json
	@-rm -rf output output.wal

clean-ingest:
	@-rm -rf ingest ingest-repo

clean-all: clean-jh clean-ingest clean-backfill

.PHONY: clean-jh clean-backfill clean-ingest clean-all docker
