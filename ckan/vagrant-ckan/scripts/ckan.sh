#!/bin/bash

# Copyright 2017 MSO4SC - javier.carnero@atos.net
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

USER='ubuntu'
 
## Required packages
apt-get install -y -qq python-dev postgresql libpq-dev python-pip python-virtualenv git-core solr-jetty openjdk-8-jdk redis-server
pip install --upgrade pip


## Install CKAN

# Create folders
mkdir -p /usr/lib/ckan/default

# Install the CKAN source code
cd /usr/lib/ckan/default
pip install -q -e 'git+https://github.com/ckan/ckan.git@ckan-2.7.0#egg=ckan'
chown -R $USER /usr/lib/ckan/default

# Install the recommended version of ‘setuptools’
pip install -r /usr/lib/ckan/default/src/ckan/requirement-setuptools.txt

# Install the Python modules that CKAN requires
pip install -r /usr/lib/ckan/default/src/ckan/requirements.txt


## Setup a PostgreSQL database

# Create a new PostgreSQL database user called ckan_default
#echo 'ckan_default' > sudo -u postgres createuser -S -D -R -P ckan_default
sudo -u postgres bash -c "psql -c \"CREATE USER ckan_default WITH PASSWORD 'ckan_default';\""

# Create a new PostgreSQL database, called ckan_default, owned by the database user we just created
sudo -u postgres createdb -O ckan_default ckan_default -E utf-8


## Create a CKAN config file

# Create directories
mkdir -p /etc/ckan/default
chown -R $USER /etc/ckan/

# Create config file
sudo -u $USER paster make-config ckan /etc/ckan/default/development.ini
sed -i -e 's/pass@localhost/ckan_default@localhost/g' /etc/ckan/default/development.ini
sed -i -e 's/ckan.site_id = default/ckan.site_id = mso4sc/g' /etc/ckan/default/development.ini
sed -i -e 's/ckan.site_url =/ckan.site_url = http:\/\/192.168.56.24:5000/g' /etc/ckan/default/development.ini


## Setup Solr

# Edit jetty configuration
sed -i -e 's/#JETTY_HOST=$(uname -n)/JETTY_HOST=127.0.0.1/g' /etc/default/jetty8
sed -i -e 's/#JETTY_PORT=8080/JETTY_PORT=8983/g' /etc/default/jetty8
service jetty8 restart

# Replace solr schema with ckan's/#JETTY_HOST
mv /etc/solr/conf/schema.xml /etc/solr/conf/schema.xml.bak
ln -s /usr/lib/ckan/default/src/ckan/ckan/config/solr/schema.xml /etc/solr/conf/schema.xml

# restart solr
service jetty8 restart

# link to solr to ckan
sed -i -e 's/#solr_url =/solr_url =/g' /etc/ckan/default/development.ini


## Create database tables
cd /usr/lib/ckan/default/src/ckan
sudo -u $USER paster db init -c /etc/ckan/default/development.ini


## Set up the DataStore

# Add plugin
sed -i -e 's/ckan.plugins = stats text_view image_view recline_view/ckan.plugins = stats text_view image_view recline_view datastore/g' /etc/ckan/default/development.ini

# Create database
sudo -u postgres bash -c "psql -c \"CREATE USER datastore_default WITH PASSWORD 'datastore_default';\""
sudo -u postgres createdb -O ckan_default datastore_default -E utf-8

# Set URLs
sed -i -e 's/datastore_default:ckan_default@localhost/datastore_default:datastore_default@localhost/g' /etc/ckan/default/development.ini
sed -i -e 's/#ckan.datastore.write_url =/ckan.datastore.write_url =/g' /etc/ckan/default/development.ini
sed -i -e 's/#ckan.datastore.read_url =/ckan.datastore.read_url =/g' /etc/ckan/default/development.ini

# Set Permissions
paster --plugin=ckan datastore set-permissions --config=/etc/ckan/default/development.ini | sudo -u postgres psql --set ON_ERROR_STOP=1


## Link to who.ini
sudo -u $USER ln -s /usr/lib/ckan/default/src/ckan/who.ini /etc/ckan/default/who.ini
