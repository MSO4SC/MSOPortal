""" MSO4SC views module """

import time
import json
import yaml
import requests
from portal import settings

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse
# from django.contrib.auth import login, authenticate
# from django.contrib import messages
# from django.views.decorators.clickjacking import xframe_options_exempt

# from social_django.models import UserSocialAuth
from social_django.utils import load_strategy

from cloudify_rest_client import CloudifyClient
from cloudify_rest_client.exceptions import CloudifyClientError
from cloudify_rest_client.exceptions \
    import DeploymentEnvironmentCreationPendingError
from cloudify_rest_client.exceptions \
    import DeploymentEnvironmentCreationInProgressError
WAIT_FOR_EXECUTION_SLEEP_INTERVAL = 3


def _get_fiware_token(user):
    social = user.social_auth.get(provider='fiware')
    if int(time.time()) - social.extra_data['auth_time'] > 3600:
        strategy = load_strategy()
        social.refresh_token(strategy)
    return social.extra_data['access_token']


@login_required
def index(request):
    social_user = request.user.social_auth.get(uid=request.user.username)
    # access_token = social_user.access_token
    access_token = _get_fiware_token(request.user)
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


def _get_products(user):
    access_token = _get_fiware_token(user)
    headers = {"Authorization": "bearer " + access_token}
    url = settings.MARKETPLACE_URL + \
        "/DSProductCatalog/api/catalogManagement/v2/productSpecification"

    text_data = requests.request("GET", url, headers=headers).text
    json_data = json.loads(text_data)
    return json_data


def _get_datasets():
    url = settings.DATACATALOGUE_URL + \
        "/api/3/action/package_list"

    text_data = requests.request("GET", url).text
    json_data = json.loads(text_data)
    if json_data["success"]:
        return json_data["result"]

    return []  # TODO(emepetres) manage errors


def _get_dataset_info(request):
    dataset = request.GET.get('dataset', None)
    url = settings.DATACATALOGUE_URL + \
        "/api/rest/dataset/" + dataset

    text_data = requests.request("GET", url).text
    if text_data == "Not found":
        return JsonResponse(None)  # TODO(emepetres) manage errors

    json_data = json.loads(text_data)
    return JsonResponse(json_data)


@login_required
def experimentstool(request):
    products = _get_products(request.user)
    datasets = _get_datasets()
    context = {
        'datacatalogue_url': settings.DATACATALOGUE_URL,
        'marketplace_url': settings.MARKETPLACE_URL,
        'products': products,
        'datasets': datasets
    }
    return render(request, 'experimentstool.html', context)


def _get_client():
    client = CloudifyClient(host=settings.ORCHESTRATOR_HOST,
                            username=settings.ORCHESTRATOR_USER,
                            password=settings.ORCHESTRATOR_PASS,
                            tenant=settings.ORCHESTRATOR_TENANT)
    return client


def _upload_blueprint(path, blueprint_id):
    client = _get_client()
    try:
        blueprint = client.blueprints.upload(path, blueprint_id)
    except CloudifyClientError as e:
        print(e)
        return {'blueprint': None, 'error': str(e)}

    return {'blueprint': blueprint, 'error': None}


def _create_deployment(blueprint_id, development_id, inputs, retries=3):
    client = _get_client()
    try:
        deployment = client.deployments.create(
            blueprint_id,
            development_id,
            inputs=inputs,
            skip_plugins_validation=True
        )
    except (DeploymentEnvironmentCreationPendingError,
            DeploymentEnvironmentCreationInProgressError) as e:
        if (retries > 0):
            time.sleep(WAIT_FOR_EXECUTION_SLEEP_INTERVAL)
            return _create_deployment(blueprint_id, development_id, inputs,
                                      retries - 1)
        print(e)
        return {'deployment': None, 'error': str(e)}
    except CloudifyClientError as e:
        print(e)
        return {'deployment': None, 'error': str(e)}
    return {'deployment': deployment, 'error': None}


def _execute_deployment(development_id, workflow):
    client = _get_client()
    try:
        execution = client.executions.start(development_id, workflow)
    except CloudifyClientError as e:
        print(e)
        return {'execution': None, 'error': str(e)}
    return {'execution': execution, 'error': None}


def _install_deployment(development_id):
    return _execute_deployment(development_id, 'install')


def _run_deployment(development_id):
    return _execute_deployment(development_id, 'run_jobs')


def _uninstall_deployment(development_id):
    return _execute_deployment(development_id, 'uninstall')


def _delete_deployment(development_id, force=False):
    client = _get_client()
    try:
        deployment = client.deployments.delete(
            development_id, ignore_live_nodes=force)
    except CloudifyClientError as e:
        print(e)
        return {'deployment': None, 'error': str(e)}
    return {'deployment': deployment, 'error': None}


def _delete_blueprint(blueprint_id):
    client = _get_client()
    try:
        blueprint = client.blueprints.delete(blueprint_id)
    except CloudifyClientError as e:
        print(e)
        return {'blueprint': None, 'error': str(e)}

    return {'blueprint': blueprint, 'error': None}
