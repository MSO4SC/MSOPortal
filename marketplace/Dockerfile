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

FROM conwetlab/biz-ecosystem-logic-proxy:develop

LABEL maintainer="javier.carnero@atos.net"

## MSO4SC OAuth Hack that modifies redirect path
RUN sed -i "s|res.redirect(redirectPath)|res.redirect('http://' + process.env.PORTAL_HOST + '/marketplaceLoggedIn/')|g" /business-ecosystem-logic-proxy/server.js
