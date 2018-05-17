# Copyright 2018 MSO4SC - javier.carnero@atos.net
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

FROM conwetlab/biz-ecosystem-charging-backend:develop

LABEL maintainer="javier.carnero@atos.net"

## Package the basic url plugin and install on start
RUN apt update && apt install -y zip
RUN git clone https://github.com/FIWARE-TMForum/biz-basic-plugins.git && \
    cd biz-basic-plugins/basic-url && \
    zip basic-url.zip package.json basic_url.py

RUN sed -i '/service apache2 restart/a\
echo "Trying to install basic url plugin"\n\
touch /business-ecosystem-charging-backend/src/wstore/asset_manager/resource_plugins/plugins/__init__.py\n\
/business-ecosystem-charging-backend/src/manage.py loadplugin /business-ecosystem-charging-backend/src/biz-basic-plugins/basic-url/basic-url.zip\n\
STATUS=$?\n\
I=0\n\
while [[ ${STATUS} -ne 0  && ${I} -lt 50 ]]; do\n\
    echo "Could not install the plugin yet, retrying in 5 seconds..."\n\
\n\
    sleep 5\n\
    touch /business-ecosystem-charging-backend/src/wstore/asset_manager/resource_plugins/plugins/__init__.py\n\
    /business-ecosystem-charging-backend/src/manage.py loadplugin /business-ecosystem-charging-backend/src/biz-basic-plugins/basic-url/basic-url.zip\n\
    STATUS=$?\n\
\n\
    I=${I}+1\n\
done' /entrypoint.sh
