#!/bin/bash
set -e

systemctl restart nginx

uwsgi --socket portal.sock --module portal.wsgi --chmod-socket=664
