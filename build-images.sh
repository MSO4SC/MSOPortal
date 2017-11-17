#!/bin/bash -l
set -e

docker build --no-cache -t mso4sc/datacatalogue ckan/.
#docker build --no-cache -t mso4sc/biz-ecosystem biz-ecosystem/.

docker push mso4sc/datacatalogue
#docker push mso4sc/biz-ecosystem
