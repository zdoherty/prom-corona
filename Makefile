ingest-repo:
	git clone https://github.com/roidelapluie/ingest ingest-repo

ingest: ingest-repo
	cd ingest-repo && go build -o ../ingest

johns-hopkins/repo:
	git clone https://github.com/CSSEGISandData/COVID-19 johns-hopkins/repo

johns-hopkins/backfill.json: johns-hopkins/repo
	python johns-hopkins/convert.py backfill >johns-hopkins/backfill.json

output: ingest johns-hopkins/backfill.json
	./ingest -input-file=johns-hopkins/backfill.json
