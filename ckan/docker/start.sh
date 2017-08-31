#!/bin/bash

docker-compose start db
docker-compose start solr
docker-compose start redis
docker-compose start ckan