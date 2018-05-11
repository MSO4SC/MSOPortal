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

FROM mso4sc/ckan:2.7

LABEL maintainer="javier.carnero@atos.net"

ENV DEBIAN_FRONTEND noninteractive

## Download FIWARE IDM plugin
ADD fiware-idm-plugin.sh .
RUN chmod +x fiware-idm-plugin.sh
RUN ./fiware-idm-plugin.sh
RUN rm fiware-idm-plugin.sh
# Enable unsecure transport (not https)
ENV OAUTHLIB_INSECURE_TRANSPORT True

# Modify entrypoint to write IDM config the first time
ADD fiware-idm-plugin-config.sh /
RUN chmod +x /fiware-idm-plugin-config.sh
RUN sed -i '/ckan-paster make-config/a\
    /fiware-idm-plugin-config.sh' /ckan-entrypoint.sh


# Modify entrypoint to write IDM credentials
ADD ckan-idm-entrypoint.sh /
RUN chmod +x /ckan-idm-entrypoint.sh
RUN sed -i '/set_environment/a\
export FRONTEND_ENTRYPOINT=${FRONTEND_ENTRYPOINT}\n\
export IDM_ENTRYPOINT=${IDM_ENTRYPOINT}\n\
export FIWARE_ID=${FIWARE_ID}\n\
export FIWARE_SECRET=${FIWARE_SECRET}\n\
export CONFIG=${CONFIG}\n\
/ckan-idm-entrypoint.sh' /ckan-entrypoint.sh
