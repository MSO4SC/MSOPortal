FROM fiware/business-api-ecosystem:v5.4.1

## MSO4SC OAuth Hack
# Modify redirect path
RUN sed -i "s|res.redirect(redirectPath)|res.redirect(process.env.FRONTEND_ENTRYPOINT + '/marketplaceLoggedIn/')|g" /apis/business-ecosystem-logic-proxy/server.js

# Modify entrypoint to populate env variables
RUN sed -i '/-z $PAYPAL_CLIENT_ID/i\
if [ -z \$FRONTEND_ENTRYPOINT ];\n\
then\n\
    echo FRONTEND_ENTRYPOINT environment variable not set\n\
    exit 1\n\
else\n\
    export FRONTEND_ENTRYPOINT=\${FRONTEND_ENTRYPOINT}\n\
fi\n\
' /entrypoint.sh

RUN sed -i '/-z $PAYPAL_CLIENT_ID/i\
if [ -z \$IDM_ENTRYPOINT ];\n\
then\n\
    echo IDM_ENTRYPOINT environment variable not set\n\
    exit 1\n\
else\n\
    export IDM_ENTRYPOINT=\${IDM_ENTRYPOINT}\n\
fi\n\
' /entrypoint.sh

## Set IDM entrypoint
RUN sed -i "s|'https://account.lab.fiware.org'|process.env.IDM_ENTRYPOINT|g" /apis/business-ecosystem-logic-proxy/config.js
RUN sed -i "s|'https://account.lab.fiware.org'|process.env.IDM_ENTRYPOINT|g" /apis/business-ecosystem-logic-proxy/config.js.template
RUN sed -i "s|'https://account.lab.fiware.org'|process.env.IDM_ENTRYPOINT|g" /apis/business-ecosystem-logic-proxy/test/utils.js

RUN sed -i "s|'https://account.lab.fiware.org/oauth2/authorize'|process.env.IDM_ENTRYPOINT + '/oauth2/authorize'|g" /apis/business-ecosystem-logic-proxy/node_modules/passport-fiware-oauth/lib/passport-fiware-oauth/oauth2.js

RUN sed -i "s|'https://account.lab.fiware.org/oauth2/token'|process.env.IDM_ENTRYPOINT + '/oauth2/token'|g" /apis/business-ecosystem-logic-proxy/node_modules/passport-fiware-oauth/lib/passport-fiware-oauth/oauth2.js

RUN sed -i "s|'https://account.lab.fiware.org/user?access_token='|process.env.IDM_ENTRYPOINT + '/user?access_token='|g" /apis/business-ecosystem-logic-proxy/node_modules/passport-fiware-oauth/lib/passport-fiware-oauth/oauth2.js

#TODO
#./business-ecosystem-charging-backend/src/wstore/management/commands/configureproject.py:            print "Include Identity manager endpoint: (default https://account.lab.fiware.org/)"

#./business-ecosystem-charging-backend/src/wstore/management/commands/configureproject.py:                settings['idm_endpoint'] = "https://account.lab.fiware.org/"

#./business-ecosystem-charging-backend/src/wstore/management/commands/configureproject.py:                if settings['idm_endpoint'].startswith('https://account.lab.fiware.org'):