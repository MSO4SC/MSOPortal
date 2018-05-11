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

git clone https://github.com/ckan/ckan.git
cd ckan
git checkout 2.7

sed -i 's/version="2.7"/version="2.8"/g' ckan/config/solr/schema.xml
sed -i 's/2.7/2.8/g' ckan/lib/search/__init__.py
sed -i '/git-core \\/alibffi-dev \\' Dockerfile
#sed -i 's/VOLUME.*//g' Dockerfile

docker build . -t mso4sc/ckan
docker push mso4sc/ckan

cd ..
rm -r cka#!/bin/bash -l
set -e

git clone https://github.com/ckan/ckan.git
cd ckan
git checkout 2.7

sed -i 's/version="2.7"/version="2.8"/g' ckan/config/solr/schema.xml
sed -i 's/2.7/2.8/g' ckan/lib/search/__init__.py
sed -i '/git-core \\/alibffi-dev \\' Dockerfile
#sed -i 's/VOLUME.*//g' Dockerfile

docker build . -t mso4sc/ckan
#docker push mso4sc/ckan

cd ..
rm -r ckan
