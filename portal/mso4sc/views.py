from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AdminPasswordChangeForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth import update_session_auth_hash, login, authenticate
from django.contrib import messages

from social_django.models import UserSocialAuth

from django.views.decorators.clickjacking import xframe_options_exempt


@login_required
def index(request):
    social_user = request.user.social_auth.get(uid=request.user.username)
    access_token = social_user.access_token
    extra_data = social_user.extra_data

    return render(request, 'home.html', {'access_token': access_token, 'extra_data': extra_data})


@login_required
def marketplace_logIn(request):
    if 'marketplace' not in request.session:
        request.session['marketplace'] = False

    if request.session['marketplace']:
        return redirect('/marketplace')

    return redirect('http://localhost:8000/login')


@login_required
def marketplace_loggedIn(request):
    request.session['marketplace'] = True
    return redirect('/marketplace')


#@xframe_options_exempt
@login_required
def marketplace(request):
    if 'marketplace' not in request.session:
        request.session['marketplace'] = False

    if not request.session['marketplace']:
        return redirect('/marketplaceLogIn')

    return render(request, 'marketplace.html')
