FROM ckan/ckan:latest

ENV DEBIAN_FRONTEND noninteractive

# Solve a bug with latest ckan image
RUN ckan-pip install --upgrade -r $CKAN_VENV/src/ckan/dev-requirements.txt

## Create CKAN config file
RUN ckan-paster make-config --no-interactive ckan "${CKAN_CONFIG}/ckan.ini"

## Install FIWARE IDM plugin
USER root
ADD fiware-idm-plugin.sh .
RUN ./fiware-idm-plugin.sh [FRONT_ENTRYPOINT] [ID] [SECRET]
RUN rm fiware-idm-plugin.sh
# Enable unsecure transport (not https)
ENV OAUTHLIB_INSECURE_TRANSPORT True

## Modify entrypoint to set MSO4SC OAuth2 Hack and 

# Install gosu
RUN echo "deb http://ftp.debian.org/debian jessie-backports main" >> /etc/apt/sources.list
RUN apt-get update
RUN apt-get install -y apt-utils
RUN apt-get install -y gosu
RUN chmod +s /usr/sbin/gosu

# Add the idm docker entrypoint file
ADD ckan-idm-entrypoint.sh /
RUN chmod +x /ckan-idm-entrypoint.sh
RUN chown ckan:ckan /ckan-idm-entrypoint.sh

# Modify the entrypoint to call the idm one with root
RUN sed -i '/set_environment/i\
export FRONTEND_ENTRYPOINT=${FRONTEND_ENTRYPOINT}\n\
export BIZ_FIWARE_ID=${BIZ_FIWARE_ID}\n\
export BIZ_FIWARE_SECRET=${BIZ_FIWARE_SECRET}\n\
export CONFIG=${CONFIG}\n\
/bin/bash -c "/usr/sbin/gosu root /ckan-idm-entrypoint.sh"' /ckan-entrypoint.sh

## Modify the entrypoint to wait for db ready
ADD ckan-wait-db.sh /
RUN chmod +x /ckan-wait-db.sh
RUN chown ckan:ckan /ckan-wait-db.sh
RUN sed -i '/set_environment/a\
/bin/bash -c "/ckan-wait-db.sh"' /ckan-entrypoint.sh

USER ckan