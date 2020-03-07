venv:
	python3 -m pip install --upgrade virtualenv
	python3 -m virtualenv venv
	source venv/bin/activate
	python3 -m pip install -U pip virtualenv
	python3 -m pip install -r requirements.txt
