#!/bin/bash
set -e

echo "This script is intended to be run on Ubuntu >= 16.04, but adaptation to other distributions should be easy."

if [ "$#" -ne 1 ]; then
    echo "Usage: "$0" [python-packages-dir]"
    echo "   "$0" /usr/local/lib/python3.5/dist-packages"
    exit
fi

./setup.sh $1

pip3 install uwsgi

mkdir -p /etc/nginx/sites-available
ln -s $PWD/nginx.conf /etc/nginx/sites-available/portal_nginx.conf

apt-get install -y nginx

python3 manage.py collectstatic