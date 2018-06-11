#!/bin/bash

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

if [ "$#" -lt 2 ]; then
    echo "Usage: "$0" [email] [[host] ..]"
    exit
fi

apt-get update
apt-get install -y software-properties-common
add-apt-repository -y ppa:certbot/certbot
apt-get update
apt-get install -y certbot 

COMMAND="certbot certonly --standalone --agree-tos -m $1"
#COMMAND="certbot certonly --webroot -w ./certs --agree-tos -m $1"

for host in "${@:2}"
do
    COMMAND="$COMMAND -d $host"
done

# generate the keys
eval $COMMAND

# automatic renewal
#certbot renew --dry-run