#!/bin/bash -l

# Copyright 2018 MSO4SC - javier.carnero@atos.net
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
set -e

cd /plugins/ckanext-oauth2

## MSO4SC Hack
sed -i -e 's#toolkit.response.location = \("http.*$\|came_from\)#toolkit.response.location = "'$FRONTEND_ENTRYPOINT'/datacatalogueLoggedIn"#g' ckanext/oauth2/oauth2.py

## IDM entrypoint
sed -i -e 's|ckan.oauth2.register_url = .*$|ckan.oauth2.register_url = '$IDM_ENTRYPOINT'/users/sign_up|g' $CONFIG
sed -i -e 's|ckan.oauth2.reset_url = .*$|ckan.oauth2.reset_url = '$IDM_ENTRYPOINT'/users/password/new|g' $CONFIG
sed -i -e 's|ckan.oauth2.edit_url = .*$|ckan.oauth2.edit_url = '$IDM_ENTRYPOINT'/settings|g' $CONFIG
sed -i -e 's|ckan.oauth2.authorization_endpoint = .*$|ckan.oauth2.authorization_endpoint = '$IDM_ENTRYPOINT'/oauth2/authorize|g' $CONFIG
sed -i -e 's|ckan.oauth2.token_endpoint = .*$|ckan.oauth2.token_endpoint = '$IDM_ENTRYPOINT'/oauth2/token|g' $CONFIG
sed -i -e 's|ckan.oauth2.profile_api_url = .*$|ckan.oauth2.profile_api_url = '$IDM_ENTRYPOINT'/user|g' $CONFIG

## OAuth2 Credentials
sed -i -e 's|ckan.oauth2.client_id =.*$|ckan.oauth2.client_id = '$FIWARE_ID'|g' $CONFIG
sed -i -e 's|ckan.oauth2.client_secret =.*$|ckan.oauth2.client_secret = '$FIWARE_SECRET'|g' $CONFIG

# Reinstall OAuth2 extension
#ckan-python setup.py install
source $CKAN_HOME/bin/activate
python setup.py install
