#!/bin/sh
set -e

export IDM_PASS=${IDM_PASS}

# set idm user password
sudo sed -i "s/    'password': .*$/\    'password': '"$IDM_PASS"',/g" /horizon/openstack_dashboard/local/local_settings.py
sudo sed -i 's/set idm_password .*$/set idm_password '$IDM_PASS'/g'  expect_idm_password 

./expect_idm_password

# set email url
sudo sed -i "s|EMAIL_URL = .*$|EMAIL_URL = '"$IDM_ENTRYPOINT"'|g" /horizon/openstack_dashboard/local/local_settings.py
## TODO: CONFIGURE django backend:
# Configure these for your outgoing email host
# EMAIL_HOST = 'smtp.my-company.com'
# EMAIL_PORT = 25
# EMAIL_HOST_USER = 'djangomail'
# EMAIL_HOST_PASSWORD = 'top-secret!'

sudo /keystone/tools/with_venv.sh /keystone/bin/keystone-all -v & sudo /horizon/tools/with_venv.sh python /horizon/manage.py runserver 0.0.0.0:8000
