#!/bin/bash -l
set -e

docker build --no-cache -t mso4sc/datacatalogue datacatalogue/.
docker build --no-cache -t mso4sc/biz-ecosystem marketplace/.
docker build --no-cache -t mso4sc/idm idm/.

docker push mso4sc/datacatalogue
docker push mso4sc/biz-ecosystem
docker push mso4sc/idm
