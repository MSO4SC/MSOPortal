from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AdminPasswordChangeForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth import update_session_auth_hash, login, authenticate
from django.contrib import messages

from social_django.models import UserSocialAuth

from django.views.decorators.clickjacking import xframe_options_exempt


@login_required
def index(request):
    return render(request, 'home.html')


#@xframe_options_exempt
@login_required
def marketplace(request):
    return render(request, 'marketplace.html')
