FROM python:3

WORKDIR /usr/src/app
ENV PROM_PORT 8000
ENV INTERVAL 60

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY johns-hopkins/convert.py .

ENTRYPOINT [ "python", "./convert.py" ]
CMD ["serve"]
EXPOSE ${PROM_PORT}
