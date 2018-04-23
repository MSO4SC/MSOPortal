""" Experiments Tool views module """

import re
import json
import requests
import sso.utils

from portal import settings

# from django.core import serializers
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect
from django.http import JsonResponse

from experimentstool.models import (Application,
                                    AppInstance,
                                    WorkflowExecution,
                                    HPCInfrastructure)


@login_required
def experimentstool(request):
    context = {
        'datacatalogue_url': settings.DATACATALOGUE_URL,
        'marketplace_url': settings.MARKETPLACE_URL,
    }

    return render(request, 'experimentstool.html', context)


@login_required
def get_hpc_list(request):
    # TODO: remove passwords from response
    return JsonResponse(
        HPCInfrastructure.list(request.user, return_dict=True),
        safe=False)


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

    return JsonResponse(
        HPCInfrastructure.create(name,
                                 request.user,
                                 host,
                                 user,
                                 password,
                                 tz,
                                 HPCInfrastructure.SLURM,
                                 return_dict=True))


@login_required
def delete_hpc(request):
    pk = request.POST.get('pk', None)
    if not pk or pk == '':
        # TODO validation
        return JsonResponse({'error': 'No hpc provided'})

    return JsonResponse(
        HPCInfrastructure.remove(pk,
                                 request.user,
                                 return_dict=True))


@login_required
def get_stock(request):
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
        "/DSProductCatalog/api/catalogManagement/v2/productSpecification" + \
        "?lifecycleStatus=Launched" + \
        "&relatedParty.id=" + request.user.get_username()

    text_data = requests.request("GET", url, headers=headers).text
    json_data = json.loads(text_data)

    request.session['products'] = json_data
    request.session.modified = True

    return JsonResponse(json_data, safe=False)


@login_required
@permission_required('experimentstool.register_app')
def upload_application(request):
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

    application_path = None
    for pc in product['productSpecCharacteristic']:
        if pc['name'] == 'BLUEPRINT_PATH':
            application_path = pc['productSpecCharacteristicValue'][0]['value']
            break
    if not application_path:
        return JsonResponse({'error': 'The product does not have a ' +
                             '\'BLUEPRINT_PATH\' charasteristic'})

    return JsonResponse(Application.create(application_path,
                                           mso4sc_id,
                                           request.user,
                                           return_dict=True))


@login_required
def load_applications(request):
    return JsonResponse(
        Application.list(request.user, return_dict=True),
        safe=False)


@login_required
def get_application_inputs(request):
    application_id = int(request.GET.get('application_id', -1))

    if application_id < 0:
        return JsonResponse({'error': 'Bad application id provided'})

    return JsonResponse(Application.get_inputs(application_id,
                                               request.user,
                                               return_dict=True))


@login_required
def remove_application(request):
    application_id = int(request.POST.get('application_id', -1))

    if application_id < 0:
        return JsonResponse({'error': 'Bad application id provided'})

    return JsonResponse(Application.remove(application_id,
                                           request.user,
                                           return_dict=True))


@login_required
def get_datasets(request):
    url = settings.DATACATALOGUE_URL + \
        "/api/3/action/package_list"

    text_data = requests.request("GET", url).text
    json_data = json.loads(text_data)
    if not json_data["success"]:
        return JsonResponse([], safe=False)  # TODO(emepetres) manage errors

    request.session['datasets'] = json_data["result"]
    request.session.modified = True

    return JsonResponse(json_data["result"], safe=False)


@login_required
def get_dataset_info(request):
    if 'datasets' not in request.session:
        return JsonResponse({'error': 'No datasets loaded'})

    datasets = request.session['datasets']
    dataset_index = int(request.POST.get('dataset', -1))

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
@permission_required('experimentstool.create_instance')
def create_deployment(request):
    deployment_id = request.POST.get('deployment_id', None)
    application_id = int(request.POST.get('application_id', -1))
    inputs_str = request.POST.get('deployment_inputs', "{}")
    inputs = json.loads(inputs_str)

    if not deployment_id or deployment_id is '':
        return JsonResponse({'error': 'No instance name provided'})
    if application_id < 0:
        return JsonResponse({'error': 'No application selected'})

    hpc_list, error = HPCInfrastructure.list(request.user)
    if error is not None:
        return JsonResponse({'error': error})

    hpc_pattern = re.compile('^mso4sc_hpc_(.)*$')
    dataset_pattern = re.compile('^mso4sc_dataset_(.)*$')
    dataset_resource_pattern = re.compile('^resource_mso4sc_dataset_(.)*$')
    tosca_inputs = {}
    for _input, value in inputs.items():
        if hpc_pattern.match(_input):
            hpc_pk = value
            if hpc_pk < 0:
                # the hpc input has no configuration
                tosca_inputs[_input] = {}
                continue

            hpc = None
            for hpc_item in hpc_list:
                if hpc_item.id == hpc_pk:
                    hpc = hpc_item
                    break
            if not hpc:
                return JsonResponse({'error': 'Bad HPC provided. Please ' +
                                     'refresh and try again'})

            tosca_inputs[_input] = hpc.to_dict()
        elif dataset_pattern.match(_input):
            if 'datasets' not in request.session:
                return JsonResponse({'error': 'No datasets loaded'})
            datasets = request.session['datasets']

            # get the dataset
            dataset_index = value
            if dataset_index >= len(datasets) or dataset_index < 0:
                # the dataset input has no configuration
                tosca_inputs[_input] = ""
                continue
            dataset = _get_dataset(datasets[dataset_index])
            if 'error' in dataset:
                return JsonResponse(dataset)

            # get the resource
            if "resource_" + _input in inputs:
                dataset_resource_index = int(inputs["resource_" + _input])
            else:
                # the dataset input has no configuration
                tosca_inputs[_input] = ""
                continue

            if dataset_resource_index >= dataset["num_resources"] or \
                    dataset_resource_index < 0:
                return JsonResponse(
                    {'error': 'Bad dataset resource provided. Please ' +
                     'refresh and try again'})
            dataset_resource = dataset["resources"][dataset_resource_index]

            # finally put the url of the resource
            tosca_inputs[_input] = dataset_resource["url"]
        elif dataset_resource_pattern.match(_input):
            # Resources are managed in the dataset section above
            pass
        else:
            tosca_inputs[_input] = value

    return JsonResponse(AppInstance.create(application_id,
                                           deployment_id,
                                           tosca_inputs,
                                           request.user,
                                           return_dict=True))


@login_required
def get_deployments(request):
    return JsonResponse(
        AppInstance.list(request.user, return_dict=True),
        safe=False)


@login_required
def install_deployment(request):
    return JsonResponse(_execute_deployment(request, WorkflowExecution.INSTALL))


@login_required
def get_executions(request):
    instance_pk = int(request.GET.get('instance', -1))
    workflow = request.GET.get('workflow')
    return JsonResponse(
        WorkflowExecution.list_by_instance_workflow(
            request.user,
            instance_pk,
            workflow,
            return_dict=True),
        safe=False)


@login_required
def get_executions_events(request):
    execution_pk = int(request.GET.get('exec_id', -1))
    reset = request.GET.get("reset", "False") in ["True", "true", "TRUE"]
    offset = 0

    if execution_pk < 0:
        return JsonResponse({'error': 'Bad execution provided'})
    # TODO: check owner

    if not reset:
        offset = request.session['install_execution']['offset']

    events, error = WorkflowExecution.get_execution_events(execution_pk,
                                                           offset,
                                                           request.user)
    if error is None:
        if offset != events['last']:
            request.session['install_execution']['offset'] = \
                events.pop('last')
            request.session.modified = True

    return JsonResponse({'events': events, 'error': error})


@login_required
def run_deployment(request):
    response = _execute_deployment(request, WorkflowExecution.RUN)
    if 'error' not in response or response['error'] is None:
        request.session['run_execution'] = {
            'id': response['execution']['id'],
            'offset': 0
        }
        request.session.modified = True
    return JsonResponse(response)


@login_required
def get_run_events(request):
    if 'run_execution' not in request.session:
        return JsonResponse({'error': 'No run execution'})
    else:
        execution_id = request.session['run_execution']['id']
        reset = request.GET.get("reset", "False") in ["True", "true", "TRUE"]
        offset = 0
        if not reset:
            offset = request.session['run_execution']['offset']

        events, error = WorkflowExecution.get_execution_events(execution_id,
                                                               offset,
                                                               request.user)
        if error is None:
            if offset != events['last']:
                request.session['run_execution']['offset'] = \
                    events.pop('last')
                request.session.modified = True

    return JsonResponse({'events': events, 'error': error})


@login_required
def uninstall_deployment(request):
    response = _execute_deployment(request, WorkflowExecution.UNINSTALL)
    if 'error' not in response or response['error'] is None:
        request.session['uninstall_execution'] = {
            'id': response['execution']['id'],
            'offset': 0
        }
        request.session.modified = True
    return JsonResponse(response)


@login_required
def get_uninstall_events(request):
    if 'uninstall_execution' not in request.session:
        return JsonResponse({'error': 'No uninstall execution'})
    else:
        execution_id = request.session['uninstall_execution']['id']
        reset = request.GET.get("reset", "False") in ["True", "true", "TRUE"]
        offset = 0
        if not reset:
            offset = request.session['uninstall_execution']['offset']

        events, error = WorkflowExecution.get_execution_events(execution_id,
                                                               offset,
                                                               request.user)
        if error is None:
            if offset != events['last']:
                request.session['uninstall_execution']['offset'] = \
                    events['last']
                request.session.modified = True

    return JsonResponse({'events': events, 'error': error})


@login_required
def destroy_deployment(request):
    deployment_id = int(request.POST.get('deployment_id', -1))

    if deployment_id is None:
        return {'error': 'No deployment provided'}

    if deployment_id < 0:
        return {'error': 'Bad deployment provided'}

    force = bool(request.POST.get('force', False))

    response = AppInstance.remove(deployment_id,
                                  request.user,
                                  force=force,
                                  return_dict=True)
    if 'error' not in response or response['error'] is None:
        if 'install_execution' in request.session:
            request.session.pop('install_execution')
        if 'run_execution' in request.session:
            request.session.pop('run_execution')
        if 'uninstall_execution' in request.session:
            request.session.pop('uninstall_execution')
        request.session.modified = True
    return JsonResponse(response)


def _execute_deployment(request, operation):
    deployment_id = int(request.POST.get('deployment_id', -1))

    if deployment_id is None:
        return {'error': 'No deployment provided'}

    if deployment_id < 0:
        return {'error': 'Bad deployment provided'}

    force = bool(request.POST.get('force', False))

    return WorkflowExecution.create(deployment_id,
                                    operation,
                                    request.user,
                                    force=force,
                                    return_dict=True)


def _get_dataset(dataset_name):
    url = settings.DATACATALOGUE_URL + \
        "/api/3/action/package_search?q=" + \
        dataset_name

    text_data = requests.request("GET", url).text
    json_data = json.loads(text_data)
    if not json_data["success"]:
        return {'error': json_data['result']}

    response = json_data["result"]
    if response["count"] <= 0:
        return {'error': "No data found"}
    # elif response["count"] == 1:
    #    return response["results"][0]
    else:
        for dataset in response["results"]:
            if dataset["name"] == dataset_name:
                return dataset

    return {'error': "No dataset match"}
