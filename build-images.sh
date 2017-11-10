#!/bin/bash -l
set -e

docker build --no-cache -t mso4sc/ckan ckan/.
docker build --no-cache -t mso4sc/biz-ecosystem biz-ecosystem/.

docker push mso4sc/ckan
docker push mso4sc/biz-ecosystem
