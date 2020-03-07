FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY johns-hopkins/convert.py .
ENV PROM_PORT 8000
CMD [ "python", "./convert.py", "serve" ]
EXPOSE ${PROM_PORT}
