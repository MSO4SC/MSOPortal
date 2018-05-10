#!/bin/bash

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
CKAN_CONFIG_FILE="${CKAN_CONFIG}/production.ini"

## OAuth2 (Fiware IDM) extension
mkdir /plugins
cd /plugins

# Extension & MSO4SC OAuth2 hack
git clone https://github.com/conwetlab/ckanext-oauth2
cd ckanext-oauth2
git checkout fiware_migration
