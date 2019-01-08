# pull official base image
FROM python:3.7-alpine

# set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set work directory
WORKDIR /portal

# install psycopg2 (https://github.com/psycopg/psycopg2/issues/684)
RUN apk update \
    && apk add --virtual build-deps gcc python3-dev musl-dev \
    && apk add postgresql-dev \
    && pip install psycopg2 \
    && apk del build-deps

# copy application
COPY portal/* /portal/
COPY docker/entrypoint.sh /entrypoint.sh

# setup dependencies
RUN pip install --upgrade pip
RUN ./setup.sh /usr/local/lib/python3.7/dist-packages

ENTRYPOINT ["/entrypoint.sh"]
