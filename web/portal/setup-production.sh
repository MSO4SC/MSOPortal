#!/bin/bash
set -e

echo "Please be sure that DEBUG=False at portal/settings.ini"

if [ "$#" -ne 1 ]; then
    echo "Usage: "$0" [python-packages-dir]"
    echo "   "$0" /usr/local/lib/python3.5/dist-packages"
    exit
fi

./setup.sh $1

apt-get update
apt-get install -y selinux-utils

apt-get install -y libpcre3 libpcre3-dev
pip3 install uwsgi

apt-get install -y nginx
sed -i 's/user www-data/user root/g' /etc/nginx/nginx.conf

ln -s $PWD/nginx.conf /etc/nginx/sites-available/portal_nginx.conf
ln -s /etc/nginx/sites-available/portal_nginx.conf /etc/nginx/sites-enabled/portal_nginx.conf

python3 manage.py collectstatic
