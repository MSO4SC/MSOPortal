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
CKAN_CONFIG_FILE="${CKAN_CONFIG}/ckan.ini"

RUN sed -i "s|ckan.auth.create_unowned_dataset = false|ckan.auth.create_unowned_dataset = true|g" $CKAN_CONFIG_FILE
RUN sed -i "s|ckan.auth.create_dataset_if_not_in_organization = false|ckan.auth.create_dataset_if_not_in_organization = true|g" $CKAN_CONFIG_FILE
RUN sed -i "s|ckan.auth.user_create_organizations = false|ckan.auth.user_create_organizations = true|g" $CKAN_CONFIG_FILE
RUN sed -i "s|ckan.auth.user_create_groups = false|ckan.auth.user_create_groups = true|g" $CKAN_CONFIG_FILE
