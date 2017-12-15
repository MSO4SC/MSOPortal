#!/bin/bash -l

docker exec -t datacatalogue bash -c 'source /usr/lib/ckan/default/bin/activate && cd /usr/lib/ckan/default/src/ckan && ckan-paster sysadmin add '$1' -c "${CKAN_CONFIG}"/ckan.ini'