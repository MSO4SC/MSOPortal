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

# Stop apache before installing anything
service apache2 stop

# Create a production.ini file
cp /etc/ckan/default/development.ini /etc/ckan/default/production.ini

# Install Apache, modwsgi, modrpaf, nginx, postfix
apt-get install -y -qq apache2 libapache2-mod-wsgi libapache2-mod-rpaf

# Install nginx
apt-get install -y -qq nginx

# Install an email server
debconf-set-selections <<< "postfix postfix/mailname string localhost"
debconf-set-selections <<< "postfix postfix/main_mailer_type string 'Internet Site'"
apt-get install -y -qq postfix

# Create the WSGI script file

# TODO http://docs.ckan.org/en/latest/maintaining/installing/deployment.html