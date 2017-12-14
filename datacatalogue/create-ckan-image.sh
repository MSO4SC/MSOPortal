#!/bin/bash -l
set -e

git clone https://github.com/ckan/ckan.git
cd ckan
git checkout tags/ckan-2.7.2

sed -i 's/version="2.7"/version="2.8"/g' ckan/config/solr/schema.xml
sed -i 's/2.7/2.8/g' ckan/lib/search/__init__.py
sed -i '/git-core \\/alibffi-dev \\' Dockerfile
#sed -i 's/VOLUME.*//g' Dockerfile

docker build . -t mso4sc/ckan
docker push mso4sc/ckan

cd ..
rm -r ckan