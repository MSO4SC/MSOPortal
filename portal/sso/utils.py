""" Common functions module """

import time
# from django.contrib.auth import login, authenticate
# from django.contrib import messages
# from django.views.decorators.clickjacking import xframe_options_exempt

from social_django.models import UserSocialAuth
from social_django.utils import load_strategy


def get_token(user):
    social = user.social_auth.get(provider='fiware')
    return social.get_access_token(load_strategy())


def get_expiration_time(user):
    social = user.social_auth.get(provider='fiware')
    diff = social.extra_data['expires'] - \
        (int(time.time()) - social.extra_data['auth_time'])
    if diff < 0:
        diff = 0
    return diff


def get_uid(user):
    social = user.social_auth.get(provider='fiware')
    return social.extra_data['uid']


def get_roles_names(user):
    """ Returns the user roles, in the app and in the organizations """
    roles_dict = {}
    social = user.social_auth.get(provider='fiware')
    if social.extra_data['roles'] is not None:
        for role in social.extra_data['roles']:
            roles_dict[role['name']] = True

    for organization in social.extra_data['organizations']:
        if organization['roles'] is not None:
            for role in organization['roles']:
                roles_dict[role['name']] = True

    return list(roles_dict.keys())


def get_social_user(user):
    try:
        fiware_login = user.social_auth.get(provider='fiware')
    except UserSocialAuth.DoesNotExist:
        fiware_login = None
    return fiware_login
