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


## OAuth2 (Fiware IDM) extension

# Install extension
git clone https://github.com/conwetlab/ckanext-oauth2
cd ckanext-oauth2
git checkout fiware_migration
python setup.py install

# Add plugin
sed -i -e 's/ckan.plugins =/ckan.plugins = oauth2/g' /etc/ckan/default/development.ini
sed -i -e 's/## Search Settings/## OAuth2 configuration\
ckan.oauth2.logout_url = /user/logged_out\
ckan.oauth2.register_url = https:\/\/account.lab.fiware.org\/users\/sign_up\
ckan.oauth2.reset_url = https:\/\/account.lab.fiware.org\/users\/password\/new\
ckan.oauth2.edit_url = https:\/\/account.lab.fiware.org\/settings\
ckan.oauth2.authorization_endpoint = https:\/\/account.lab.fiware.org\/oauth2\/authorize\
ckan.oauth2.token_endpoint = https:\/\/account.lab.fiware.org\/oauth2\/token\
ckan.oauth2.profile_api_url = https:\/\/account.lab.fiware.org\/user\
ckan.oauth2.client_id = b4f8383926a44b24823d6b2bbf055f2e\
ckan.oauth2.client_secret = f2d5b4dd81454e2684a7cc3ff8c36b56\
ckan.oauth2.scope = profile other.scope\
ckan.oauth2.rememberer_name = auth_tkt\
ckan.oauth2.profile_api_user_field = id\
ckan.oauth2.profile_api_fullname_field = displayName\
ckan.oauth2.profile_api_mail_field = email\
ckan.oauth2.authorization_header = Bearer\
\
## Search Settings/g' /etc/ckan/default/development.ini

sed -i -e 's/## Search Settings/## OAuth2 configuration\
\
ckan.oauth2.logout_url = \/user\/logged_out\
ckan.oauth2.register_url = https:\/\/account.lab.fiware.org\/users\/sign_up\
ckan.oauth2.reset_url = https:\/\/account.lab.fiware.org\/users\/password\/new\
ckan.oauth2.edit_url = https:\/\/account.lab.fiware.org\/settings\
ckan.oauth2.authorization_endpoint = https:\/\/account.lab.fiware.org\/oauth2\/authorize\
ckan.oauth2.token_endpoint = https:\/\/account.lab.fiware.org\/oauth2\/token\
ckan.oauth2.profile_api_url = https:\/\/account.lab.fiware.org\/user\
ckan.oauth2.client_id = b4f8383926a44b24823d6b2bbf055f2e\
ckan.oauth2.client_secret = f2d5b4dd81454e2684a7cc3ff8c36b56\
ckan.oauth2.scope = profile other.scope\
ckan.oauth2.rememberer_name = auth_tkt\
ckan.oauth2.profile_api_user_field = id\
ckan.oauth2.profile_api_fullname_field = displayName\
ckan.oauth2.profile_api_mail_field = email\
ckan.oauth2.authorization_header = Bearer\
\
## Search Settings/g' /etc/ckan/default/development.ini

# Enable unsecure transport (not https)
##