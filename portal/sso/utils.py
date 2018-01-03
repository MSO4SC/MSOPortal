""" Common functions module """

import time
# from django.contrib.auth import login, authenticate
# from django.contrib import messages
# from django.views.decorators.clickjacking import xframe_options_exempt

# from social_django.models import UserSocialAuth
# from social_django.utils import load_strategy


def get_token(user, from_url):
    social = user.social_auth.get(provider='fiware')
    if int(time.time()) - social.extra_data['auth_time'] > 3600:
        # strategy = load_strategy()
        # social.refresh_token(strategy)
        return (False, '/oauth/login/fiware?next=' + from_url)
    return (True, social.extra_data['access_token'])
