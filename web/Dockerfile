# pull official base image
FROM python:3.7-alpine

# set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set work directory
WORKDIR /portal

# Dependencies to install the python packages
RUN apk update && \
    apk add --virtual build-deps gcc python3-dev musl-dev libffi-dev make

# install psycopg2 (https://github.com/psycopg/psycopg2/issues/684)
RUN apk add postgresql-dev && pip install psycopg2

# copy application
COPY portal/ /portal/
RUN chmod -R +x /portal/*.sh
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# setup dependencies
RUN pip install --upgrade pip
RUN ./setup.sh /usr/local/lib/python3.7/site-packages

RUN apk del build-deps

ENTRYPOINT ["/entrypoint.sh"]
