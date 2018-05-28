""" Common functions module """

import time
import logging

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponsePermanentRedirect
from django.contrib.auth import logout

from social_django.models import UserSocialAuth
from social_django.utils import load_strategy


# Get an instance of a logger
logger = logging.getLogger(__name__)


def token_required(view):
    @login_required
    def wrap(request, *args, **kwargs):
        response = get_token(request)

        if token_need_to_redirect(response):
            return response

        return view(request, token=response, *args, **kwargs)

    return wrap


def get_token(request):
    user = request.user
    from_url = request.get_full_path()
    try:
        social = user.social_auth.get(provider='fiware')
        return social.get_access_token(load_strategy())
    except Exception as excp:
        logger.warn("Couldn't get token: "+str(excp))
        logout(request)
        return redirect('/oauth/login/fiware?next=' + from_url, permanent=True)


def token_need_to_redirect(response):
    return isinstance(response, HttpResponsePermanentRedirect)


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

    if social.extra_data['organizations'] is not None:
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
