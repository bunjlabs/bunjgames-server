FROM python:3.8

RUN apt-get update && apt-get install cron -y
RUN pip install --upgrade pip

WORKDIR /srv/server

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . /srv/server

ENTRYPOINT ["/srv/server/entrypoint.sh"]
