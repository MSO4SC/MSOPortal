#!/bin/bash
set -e

uwsgi --socket portal.sock --module portal.wsgi --chmod-socket=664

/etc/init.d/nginx restart