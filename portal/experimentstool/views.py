""" Experiments Tool views module """

import time
import json
import requests
import sso.utils

from urllib.parse import urlparse
from portal import settings

from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.forms.models import model_to_dict

from cloudify_rest_client import CloudifyClient
from cloudify_rest_client.executions import Execution
from cloudify_rest_client.exceptions import CloudifyClientError
from cloudify_rest_client.exceptions \
    import DeploymentEnvironmentCreationPendingError
from cloudify_rest_client.exceptions \
    import DeploymentEnvironmentCreationInProgressError

from experimentstool.models import HPCInfrastructure

WAIT_FOR_EXECUTION_SLEEP_INTERVAL = 3


@login_required
def experimentstool(request):
    context = {
        'datacatalogue_url': settings.DATACATALOGUE_URL,
        'marketplace_url': settings.MARKETPLACE_URL,
    }

    return render(request, 'experimentstool.html', context)


@login_required
def get_hpc_list(request):
    try:
        hpc_list = serializers.serialize(
            'json',
            HPCInfrastructure.objects.filter(owner=request.user)
        )
    except HPCInfrastructure.DoesNotExist:
        hpc_list = []
    return JsonResponse(hpc_list, safe=False)


@login_required
def add_hpc(request):
    name = request.POST.get('name', None)
    if not name or name == '':
        # TODO validation
        return JsonResponse({'error': 'No name provided'})

    host = request.POST.get('host', None)
    if not host or host == '':
        # TODO validation
        return JsonResponse({'error': 'No host provided'})

    user = request.POST.get('user', None)
    if not user or user == '':
        # TODO validation
        return JsonResponse({'error': 'No user provided'})

    password = request.POST.get('password', None)
    if not password or password == '':
        return JsonResponse({'error': 'No password provided'})

    tz = request.POST.get('timezone', None)
    if not tz or tz == '':
        # TODO validation
        return JsonResponse({'error': 'No time zone provided'})

    return JsonResponse(_add_hpc(name,
                                 request.user,
                                 host, user,
                                 password,
                                 tz,
                                 HPCInfrastructure.SLURM))


@login_required
def delete_hpc(request):
    pk = request.POST.get('pk', None)
    if not pk or pk == '':
        # TODO validation
        return JsonResponse({'error': 'No name provided'})

    return JsonResponse(_delete_hpc(request.user, pk))


@login_required
def get_products(request):
    valid, data = sso.utils.get_token(request.user, request.get_full_path())
    if valid:
        access_token = data
    else:
        # FIXME Cross-Origin Request Blocked: The Same Origin Policy disallows
        # reading the remote resource at https://account.lab.fiware.org/oauth2/
        #   authorize?client_id=859680e0c8cb4c65b5d2d6fb99ef1595&redirect_uri=
        #   http://localhost:8000/oauth/complete/fiware/&state=eXpNpKJ5jqsZoOB
        #   cm0X1hLcmaSCNoa3E&response_type=code.
        #   (Reason: CORS header ‘Access-Control-Allow-Origin’ missing).
        return redirect(data)
    headers = {"Authorization": "bearer " + access_token}
    url = settings.MARKETPLACE_URL + \
        "/DSProductCatalog/api/catalogManagement/v2/productSpecification"

    text_data = requests.request("GET", url, headers=headers).text
    json_data = json.loads(text_data)

    request.session['products'] = json_data
    return JsonResponse(json_data, safe=False)


@login_required
def upload_blueprint(request):
    if 'products' not in request.session:
        return JsonResponse({'error': 'No products loaded'})

    products = request.session['products']
    product_id = request.POST.get('product', None)
    if not product_id:
        return JsonResponse({'error': 'No product id provided'})

    mso4sc_id = request.POST.get('mso_id', None)
    if not mso4sc_id or mso4sc_id == '':
        # TODO validation
        return JsonResponse({'error': 'No mso4sc id provided'})

    product = None
    for p in products:
        if p["id"] == product_id:
            product = p
            break
    if not product:
        return JsonResponse({'error': 'Product not found'})

    blueprint_path = None
    for pc in product['productSpecCharacteristic']:
        if pc['name'] == 'BLUEPRINT_PATH':
            blueprint_path = pc['productSpecCharacteristicValue'][0]['value']
            break
    if not blueprint_path:
        return JsonResponse({'error': 'The product does not have a ' +
                             '\'BLUEPRINT_PATH\' charasteristic'})

    return JsonResponse(_upload_blueprint(blueprint_path, mso4sc_id))


@login_required
def load_blueprints(request):
    response = _get_blueprints()

    if 'error' not in response:
        request.session['blueprints'] = response['blueprints']
    return JsonResponse(response)


@login_required
def get_blueprint_inputs(request):
    if 'blueprints' not in request.session:
        return {'error': 'No blueprints loaded'}

    blueprints = request.session['blueprints']
    blueprint_index = int(request.GET.get('blueprint_index', -1))

    if blueprint_index >= len(blueprints) or blueprint_index < 0:
        return JsonResponse({'error': 'Bad blueprint index provided'})

    blueprint_id = blueprints[blueprint_index]['id']

    return JsonResponse(_get_blueprint_inputs(blueprint_id))


@login_required
def get_datasets(request):
    url = settings.DATACATALOGUE_URL + \
        "/api/3/action/package_list"

    text_data = requests.request("GET", url).text
    json_data = json.loads(text_data)
    if not json_data["success"]:
        return JsonResponse([], safe=False)  # TODO(emepetres) manage errors

    request.session['datasets'] = json_data["result"]
    return JsonResponse(json_data["result"], safe=False)


@login_required
def get_dataset_info(request):
    if 'datasets' not in request.session:
        return {'error': 'No datasets loaded'}

    datasets = request.session['datasets']
    dataset_index = int(request.GET.get('dataset', -1))

    if dataset_index >= len(datasets) or dataset_index < 0:
        return JsonResponse({'error': 'Bad dataset index provided'})

    dataset = datasets[dataset_index]

    url = settings.DATACATALOGUE_URL + \
        "/api/rest/dataset/" + dataset

    text_data = requests.request("GET", url).text
    if text_data == "Not found":
        return JsonResponse(None)  # TODO(emepetres) manage errors

    json_data = json.loads(text_data)
    return JsonResponse(json_data, safe=False)


@login_required
def create_deployment(request):
    if 'blueprints' not in request.session:
        return {'error': 'No blueprints loaded'}
    if 'datasets' not in request.session:
        return {'error': 'No datasets loaded'}

    blueprints = request.session['blueprints']
    # datasets = request.session['datasets']

    blueprint_index = int(request.POST.get('blueprint_index', -1))
    # dataset_index = int(request.POST.get('dataset_index', -1))
    inputs_str = request.POST.get('deployment_inputs', "{}")
    inputs = json.loads(inputs_str)
    deployment_id = request.POST.get('deployment_id', None)

    if blueprint_index >= len(blueprints) or blueprint_index < 0:
        return JsonResponse({'error': 'Bad blueprint index provided'})
    # if dataset_index >= len(datasets) or dataset_index < 0:
    #    return JsonResponse({'error': 'Bad dataset index provided'})
    if not deployment_id or deployment_id is '':
        return JsonResponse({'error': 'No deployment provided'})

    blueprint_id = blueprints[blueprint_index]['id']
    # dataset = datasets[dataset_index]  # TODO

    return JsonResponse(_create_deployment(blueprint_id, deployment_id, inputs))


@login_required
def get_deployments(request):
    client = _get_client()
    try:
        deployments = client.deployments.list().items
    except CloudifyClientError as e:
        print(e)
        return JsonResponse({'error': str(e)})

    request.session['deployments'] = deployments
    return JsonResponse({'deployments': deployments})


@login_required
def install_deployment(request):
    response = _execute_deployment(request, _install_deployment)
    if 'error' not in response:
        request.session['install_execution'] = {
            'id': response['execution']['id'],
            'offset': 0
        }
    return JsonResponse(response)


@login_required
def get_install_events(request):
    if 'install_execution' not in request.session:
        response = {'error': 'No install execution'}
    else:
        execution_id = request.session['install_execution']['id']
        reset = request.GET.get("reset", "False") in ["True", "true", "TRUE"]
        offset = 0
        if not reset:
            offset = request.session['install_execution']['offset']

        response = _get_execution_events(execution_id, offset)
        if offset != response['last']:
            request.session['install_execution']['offset'] = response.pop(
                'last')
            request.session.modified = True
            print("new offset: " +
                  str(request.session['install_execution']['offset']))

    return JsonResponse(response)


@login_required
def run_deployment(request):
    response = _execute_deployment(request, _run_deployment)
    if 'error' not in response:
        request.session['run_execution'] = {
            'id': response['execution']['id'],
            'offset': 0
        }
    return JsonResponse(response)


@login_required
def get_run_events(request):
    if 'run_execution' not in request.session:
        response = {'error': 'No run execution'}
    else:
        execution_id = request.session['run_execution']['id']
        reset = request.GET.get("reset", "False") in ["True", "true", "TRUE"]
        offset = 0
        if not reset:
            offset = request.session['run_execution']['offset']

        response = _get_execution_events(execution_id, offset)
        if offset != response['last']:
            request.session['run_execution']['offset'] = response.pop('last')
            request.session.modified = True

    return JsonResponse(response)


@login_required
def uninstall_deployment(request):
    response = _execute_deployment(request, _uninstall_deployment)
    if 'error' not in response:
        request.session['uninstall_execution'] = {
            'id': response['execution']['id'],
            'offset': 0
        }
    return JsonResponse(response)


@login_required
def get_uninstall_events(request):
    if 'uninstall_execution' not in request.session:
        response = {'error': 'No uninstall execution'}
    else:
        execution_id = request.session['uninstall_execution']['id']
        reset = request.GET.get("reset", "False") in ["True", "true", "TRUE"]
        offset = 0
        if not reset:
            offset = request.session['uninstall_execution']['offset']

        response = _get_execution_events(execution_id, offset)
        if offset != response['last']:
            request.session['uninstall_execution']['offset'] = response['last']
            request.session.modified = True

    return JsonResponse(response)


@login_required
def destroy_deployment(request):
    response = _execute_deployment(request, _destroy_deployment)
    if 'error' not in response:
        if 'install_execution' in request.session:
            request.session.pop('install_execution')
        if 'run_execution' in request.session:
            request.session.pop('run_execution')
        if 'uninstall_execution' in request.session:
            request.session.pop('uninstall_execution')
    return JsonResponse(response)


def _execute_deployment(request, operation):
    if 'deployments' not in request.session:
        return {'error': 'No deployments loaded'}

    deployments = request.session['deployments']

    deployment_index = int(request.POST.get('deployment_index', -1))

    if deployment_index is None:
        return {'error': 'No deployment provided'}

    if deployment_index >= len(deployments) or deployment_index < 0:
        return {'error': 'Bad deployment index provided'}

    deployment = deployments[deployment_index]['id']
    return operation(deployment)


@login_required
def remove_blueprint(request):
    if 'blueprints' not in request.session:
        return {'error': 'No blueprints loaded'}

    blueprints = request.session['blueprints']

    blueprint_index = int(request.POST.get('blueprint_index', -1))

    if blueprint_index is None:
        return JsonResponse({'error': 'No blueprint provided'})

    if blueprint_index >= len(blueprints) or blueprint_index < 0:
        return JsonResponse({'error': 'Bad blueprint index provided'})

    blueprint = blueprints[blueprint_index]['id']
    return JsonResponse(_remove_blueprint(blueprint))


def _add_hpc(name, owner, host, user, password, tz, manager):
    hpc = HPCInfrastructure.objects.create(name=name,
                                           owner=owner,
                                           host=host,
                                           user=user,
                                           password=password,
                                           time_zone=tz,
                                           manager=manager)
    return {'hpc': model_to_dict(hpc)}


def _delete_hpc(owner, pk):
    try:
        hpc = HPCInfrastructure.objects.get(pk=pk)
        if (owner == hpc.owner):
            hpc.delete()
            return {'hpc': model_to_dict(hpc)}
        else:
            return {'error': 'HPC does not belong to user'}
    except HPCInfrastructure.DoesNotExist:
        return {'error': 'HPC does not exists'}


def _get_client():
    client = CloudifyClient(host=settings.ORCHESTRATOR_HOST,
                            username=settings.ORCHESTRATOR_USER,
                            password=settings.ORCHESTRATOR_PASS,
                            tenant=settings.ORCHESTRATOR_TENANT)
    return client


def _upload_blueprint(path, blueprint_id):
    is_url = bool(urlparse(path).scheme)

    client = _get_client()
    try:
        if is_url:
            blueprint = client.blueprints.publish_archive(path, blueprint_id)
        else:
            blueprint = client.blueprints.upload(path, blueprint_id)
    except CloudifyClientError as e:
        print(e)
        return {'error': str(e)}

    return {'blueprint': blueprint}


def _get_blueprints():
    client = _get_client()
    try:
        blueprints = client.blueprints.list().items
    except CloudifyClientError as e:
        print(e)
        return {'error': str(e)}

    return {'blueprints': blueprints}


def _get_blueprint_inputs(blueprint_id):
    client = _get_client()
    try:
        blueprint_dict = client.blueprints.get(blueprint_id)
        inputs = blueprint_dict['plan']['inputs']
        data = [{'name': name,
                 'type': input.get('type', '-'),
                 'default': input.get('default', '-'),
                 'description': input.get('description', '-')}
                for name, input in inputs.items()]
    except CloudifyClientError as e:
        print(e)
        return {'error': str(e)}
    return {'inputs': data}


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
        return {'error': str(e)}
    except CloudifyClientError as e:
        print(e)
        return {'error': str(e)}
    return {'deployment': deployment}


def _install_deployment(development_id):
    return _execute_workflow(development_id, 'install')


def _run_deployment(development_id):
    return _execute_workflow(development_id, 'run_jobs')


def _uninstall_deployment(development_id):
    return _execute_workflow(development_id, 'uninstall')


def _execute_workflow(development_id, workflow):
    client = _get_client()
    try:
        execution = client.executions.start(development_id, workflow)
    except CloudifyClientError as e:
        return {'error': str(e)}
    return {'execution': execution}


def _get_execution_events(execution_id, offset):
    client = _get_client()

    execution = client.executions.get(execution_id)
    events = client.events.list(execution_id=execution_id,
                                _offset=offset,
                                _size=100)
    last_message = events.metadata.pagination.total

    return {
        'events': _events_to_string(events.items),
        'last': last_message,
        'status': execution.status,
        'finished': _is_execution_finished(execution.status)
    }


def _events_to_string(events):
    response = []
    for event in events:
        print(json.dumps(event))
        event_type = event["type"]
        message = ""
        if event_type == "cloudify_event":
            cloudify_event_type = event["event_type"]
            message = event["reported_timestamp"] + \
                " " + event["message"]
            if cloudify_event_type == "workflow_node_event":
                message += " " + event["node_instance_id"] + \
                    " (" + event["node_name"] + ")"
            elif cloudify_event_type == "sending_task" \
                    or cloudify_event_type == "task_started" \
                    or cloudify_event_type == "task_succeeded" \
                    or cloudify_event_type == "task_failed":
                # message += " [" + event["operation"] + "]"
                if event["node_instance_id"]:
                    message += " " + event["node_instance_id"]
                if event["node_name"]:
                    message += " (" + event["node_name"] + ")"
            elif cloudify_event_type == "workflow_started" \
                    or cloudify_event_type == "workflow_succeeded" \
                    or cloudify_event_type == "workflow_failed" \
                    or cloudify_event_type == "workflow_cancelled":
                pass
            else:
                message = json.dumps(event)
            if event["error_causes"]:
                for cause in event["error_causes"]:
                    message += "\n" + cause['type'] + ": " + cause["message"]
                    message += "\n\t" + cause["traceback"]
        else:
            message = json.dumps(event)
        response.append(message)

    return response


def _is_execution_finished(status):
    return status in Execution.END_STATES


def _destroy_deployment(development_id, force=False):
    client = _get_client()
    try:
        deployment = client.deployments.delete(
            development_id, ignore_live_nodes=force)
    except CloudifyClientError as e:
        print(e)
        return {'error': str(e)}
    return {'deployment': deployment}


def _remove_blueprint(blueprint_id):
    client = _get_client()
    try:
        blueprint = client.blueprints.delete(blueprint_id)
    except CloudifyClientError as e:
        print(e)
        return {'error': str(e)}

    return {'blueprint': blueprint}
