#!/bin/bash -l
set -e

cd /mso4sc/ckanext-oauth2

## MSO4SC Hack
sed -i -e 's|toolkit.response.location = .*$|toolkit.response.location = "$FRONTEND_ENTRYPOINT/datacatalogueLoggedIn"|g' ckanext/oauth2/oauth2.py

## OAuth2 Credentials
sed -i -e 's|ckan.oauth2.client_id =.*$|ckan.oauth2.client_id = '$FIWARE_ID'|g' $CONFIG
sed -i -e 's|ckan.oauth2.client_secret =.*$|ckan.oauth2.client_secret = '$FIWARE_SECRET'|g' $CONFIG

# Reinstall OAuth2 extension
$CKAN_VENV/bin/python setup.py install
