#!/bin/sh
set -e

export IDM_PASS=${IDM_PASS}

# set idm user password
sudo sed -i "s/    'password':.*$/\    'password':'"$IDM_PASS"',/g" /horizon/openstack_dashboard/local/local_settings.py
sudo sed -i 's/set idm_password .*$/set idm_password '$IDM_PASS'/g'  expect_idm_password 
./expect_idm_password

sudo /keystone/tools/with_venv.sh /keystone/bin/keystone-all -v & sudo /horizon/tools/with_venv.sh python /horizon/manage.py runserver 0.0.0.0:8000
