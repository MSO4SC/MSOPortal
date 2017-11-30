# Copyright 2017 MSO4SC - javier.carnero@atos.net
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM ubuntu:14.04

LABEL maintainer="javier.carnero@atos.net"

ENV HOME=/
ENV IDM_PASS=mso4scpower

# Install Ubuntu dependencies
RUN sudo apt-get update && \
    sudo apt-get install -y wget python git vim expect && \
    wget https://bootstrap.pypa.io/get-pip.py && \
    sudo python get-pip.py

# Install Ubuntu project dependencies
RUN sudo apt-get install -y python-dev python-virtualenv libssl-dev libffi-dev libjpeg8-dev libxml2-dev libxslt1-dev libsasl2-dev libssl-dev libldap2-dev libffi-dev libsqlite3-dev libmysqlclient-dev python-mysqldb

# Download latest version of the code 
RUN git clone https://github.com/ging/keystone
    
RUN git clone https://github.com/ging/horizon

# Configuring settings files
RUN cp keystone/etc/keystone.conf.sample keystone/etc/keystone.conf && \
    cp horizon/openstack_dashboard/local/local_settings.py.example horizon/openstack_dashboard/local/local_settings.py && \
    sed -i s/\$\$IDM_PASS/${IDM_PASS}/g horizon/openstack_dashboard/local/local_settings.py

# Install python dependecies
RUN sudo python keystone/tools/install_venv.py && \
    sudo python horizon/tools/install_venv.py

WORKDIR keystone

# Sync database
RUN sudo tools/with_venv.sh bin/keystone-manage db_sync && \
    sudo tools/with_venv.sh bin/keystone-manage db_sync --extension=endpoint_filter && \
    sudo tools/with_venv.sh bin/keystone-manage db_sync --extension=oauth2 && \
    sudo tools/with_venv.sh bin/keystone-manage db_sync --extension=roles && \
    sudo tools/with_venv.sh bin/keystone-manage db_sync --extension=user_registration && \
    sudo tools/with_venv.sh bin/keystone-manage db_sync --extension=two_factor_auth

# Prepare to set up idm password
COPY expect_idm_password .
RUN sed -i s/\$\$IDM_PASS/${IDM_PASS}/g expect_idm_password && \
    chmod +x expect_idm_password && \
    sudo ./expect_idm_password

# Mount volumes to grant access from host
VOLUME /keystone/
VOLUME /horizon/

### Exposed ports
# - Keystone
EXPOSE 5000
# - Horizon (HTTP)
EXPOSE 8000

CMD sudo /keystone/tools/with_venv.sh /keystone/bin/keystone-all -v & sudo /horizon/tools/with_venv.sh python /horizon/manage.py runserver 0.0.0.0:8000