""" MSO4SC views module """

import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import Group
from django.http import JsonResponse

import sso.utils
from sso.utils import token_required

from portal import settings


# Get an instance of a logger
logger = logging.getLogger(__name__)


def index(request):
    if request.user.is_authenticated:
        access_token = sso.utils.get_token(request)
        if not access_token:
            return redirect('/oauth/login/fiware?next=/', permanent=True)

        user = request.user
        social_user = sso.utils.get_social_user(user)

        # match user roles with groups
        roles = sso.utils.get_roles_names(user)
        roles.append('User')  # add User role by default
        groups = []
        for group in user.groups.all():
            if group.name not in roles:
                user.groups.remove(group)
            else:
                groups.append(group.name)
        new_groups = groups
        for role in roles:
            if role not in groups:
                try:
                    group = Group.objects.get(name=role)
                    user.groups.add(group)
                    new_groups.append(role)
                except Group.DoesNotExist:
                    logger.warn('Role '+role+' does not exists as a group.')

        # get user info
        token_expires_in = sso.utils.get_expiration_time(user)
        m, s = divmod(token_expires_in, 60)
        h, m = divmod(m, 60)
        str_expires_in = str(m) + ' minutes and ' + str(s) + ' seconds.'
        if h > 0:
            str_expires_in = '1 hour'
        extra_data = social_user.extra_data

        return render(request, 'home.html', {'access_token': access_token +
                                             ', expires in ' + str_expires_in,
                                             'groups': str(new_groups),
                                             'extra_data': extra_data})
    else:
        return render(request, 'landing.html', {})


@token_required
def marketplace_logIn(request, *args, **kwargs):
    access_token = kwargs['token']
    if not access_token:
        return JsonResponse({'redirect': kwargs['url']+'/marketplaceLogIn/'})

    if 'marketplace' not in request.session:
        request.session['marketplace'] = False

    if request.session['marketplace']:
        return redirect('/marketplace')

    return redirect(settings.MARKETPLACE_URL + '/login')


@login_required
def marketplace_loggedIn(request):
    request.session['marketplace'] = True
    return redirect('/marketplace')


@login_required
def marketplace(request):
    if 'marketplace' not in request.session:
        request.session['marketplace'] = False

    if not request.session['marketplace']:
        return redirect('/marketplaceLogIn')

    context = {'marketplace_url': settings.MARKETPLACE_URL}
    return render(request, 'marketplace.html', context)


@token_required
def datacatalogue_logIn(request, *args, **kwargs):
    access_token = kwargs['token']
    if not access_token:
        return JsonResponse({'redirect': kwargs['url']+'/datacatalogueLogIn/'})

    if 'datacatalogue' not in request.session:
        request.session['datacatalogue'] = False

    if request.session['datacatalogue']:
        return redirect('/datacatalogue')

    return redirect(settings.DATACATALOGUE_URL + '/user/login')


@login_required
def datacatalogue_loggedIn(request):
    request.session['datacatalogue'] = True
    return redirect('/datacatalogue')


@login_required
def datacatalogue(request):
    if 'datacatalogue' not in request.session:
        request.session['datacatalogue'] = False

    if not request.session['datacatalogue']:
        return redirect('/datacatalogueLogIn')

    context = {'datacatalogue_url': settings.DATACATALOGUE_URL}
    return render(request, 'datacatalogue.html', context)
