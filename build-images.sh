#!/bin/bash -l
set -e

docker build --no-cache -t mso4sc/datacatalogue datacatalogue/docker/.
docker build --no-cache -t mso4sc/marketplace marketplace/.
docker build --no-cache -t mso4sc/idm idm/docker.

docker push mso4sc/datacatalogue
docker push mso4sc/marketplace
docker push mso4sc/idm
