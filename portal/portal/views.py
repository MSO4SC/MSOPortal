""" MSO4SC views module """

import time

from portal import settings, common

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


@login_required
def index(request):
    social_user = request.user.social_auth.get(uid=request.user.username)
    # access_token = social_user.access_token
    valid, data = common.get_token(
        request.user, request.get_full_path())
    if valid:
        access_token = data
    else:
        return redirect(data)
    token_expires_in = 3600 - \
        (int(time.time()) - social_user.extra_data['auth_time'])
    m, s = divmod(token_expires_in, 60)
    h, m = divmod(m, 60)
    str_expires_in = str(m) + ' minutes and ' + str(s) + ' seconds.'
    if h > 0:
        str_expires_in = '1 hour'
    extra_data = social_user.extra_data

    return render(request, 'home.html', {'access_token': access_token +
                                         ', expires in ' + str_expires_in,
                                         'extra_data': extra_data})


@login_required
def marketplace_logIn(request):
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


@login_required
def datacatalogue_logIn(request):
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
