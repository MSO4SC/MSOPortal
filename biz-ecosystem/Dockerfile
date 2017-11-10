FROM fiware/business-api-ecosystem:latest

## MSO4SC OAuth Hack

# Modify redirect path
RUN sed -i "s|res.redirect(redirectPath)|res.redirect(process.env.FRONTEND_ENTRYPOINT + '/marketplaceLoggedIn/')|g" /apis/business-ecosystem-logic-proxy/server.js

# Modify entrypoint to populate FRONTEND_ENTRYPOINT env variable
RUN sed -i '/echo `pwd`/a\
if [ -z \$FRONTEND_ENTRYPOINT ];\n\
then\n\
    echo FRONTEND_ENTRYPOINT environment variable not set\n\
    exit 1\n\
else\n\
    export FRONTEND_ENTRYPOINT=\${FRONTEND_ENTRYPOINT}\n\
fi' /entrypoint.sh
