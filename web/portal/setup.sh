#!/bin/sh
set -e

if [ "$#" -ne 1 ]; then
    echo "Usage: "$0" [python-packages-dir]"
    echo "   "$0" /usr/local/lib/python3.5/dist-packages"
    exit
fi

pip3 install -r requirements.txt

# Hack to be python3 compatible
PYPKG=$1
sed -i 's/import urlparse/#import urlparse/g' $PYPKG/cloudify_rest_client/*.py
sed -i 's/urlparse\./urllib.parse./g' $PYPKG/cloudify_rest_client/*.py
sed -i 's/urllib\.quote/urllib.parse.quote/g' $PYPKG/cloudify_rest_client/*.py

sed -i 's/import urlparse/#import urlparse/g' $PYPKG/cloudify_rest_client/aria/*.py
sed -i 's/urlparse\./urllib.parse./g' $PYPKG/cloudify_rest_client/aria/*.py
sed -i 's/urllib\.quote/urllib.parse.quote/g' $PYPKG/cloudify_rest_client/aria/*.py

sed -i 's/urlsafe_b64encode(credentials)/urlsafe_b64encode(credentials.encode("utf-8"))/g' $PYPKG/cloudify_rest_client/client.py
sed -i 's/+ encoded_credentials/+ str(encoded_credentials, "utf-8")/g' $PYPKG/cloudify_rest_client/client.py
sed -i '/self.response = response/a\        self.message = message' $PYPKG/cloudify_rest_client/exceptions.py
