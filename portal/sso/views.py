from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AdminPasswordChangeForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth import update_session_auth_hash, login, authenticate
from django.contrib import messages

from social_django.models import UserSocialAuth

from django.conf import settings as global_settings


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            user = authenticate(
                username=form.cleaned_data.get('username'),
                password=form.cleaned_data.get('password1')
            )
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})


def login_error(request):
    return render(request, 'login_error.html')


def auth_canceled(request):
    return render(request, 'auth_canceled.html')


@login_required
def settings(request):
    user = request.user
    context = {}

    try:
        fiware_login = user.social_auth.get(provider='fiware')
        context['fiware_idm_endpoint'] = global_settings.FIWARE_IDM_ENDPOINT
    except UserSocialAuth.DoesNotExist:
        fiware_login = None
    context['fiware_login'] = fiware_login

    context['can_disconnect'] = (user.social_auth.count() >
                                 1 or user.has_usable_password())

    return render(request, 'settings.html', context)


@login_required
def password(request):
    if request.user.has_usable_password():
        PasswordForm = PasswordChangeForm
    else:
        PasswordForm = AdminPasswordChangeForm

    if request.method == 'POST':
        form = PasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(
                request, 'Your password was successfully updated!')
            return redirect('password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordForm(request.user)
    return render(request, 'password.html', {'form': form})
