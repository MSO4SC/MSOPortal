from social_django.middleware import SocialAuthExceptionMiddleware
from social_core.exceptions import AuthCanceled
import traceback


class RedirectOnCancelMiddleware(SocialAuthExceptionMiddleware):
    def get_redirect_uri(self, request, exception):
        if isinstance(exception, AuthCanceled):
            traceback.print_exc()
            return '/auth-canceled'
        else:
            return super(RedirectOnCancelMiddleware, self).get_redirect_uri(request, exception)
