""" Experiments Tool views module """

import re
import json
import requests
import tempfile
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
def get_new_stock(request):
    valid, data = sso.utils.get_token(request.user, request.get_full_path())
    if valid:
        access_token = data
    else:
        # FIXME: Cross-Origin Request Blocked: The Same Origin Policy disallows
        # reading the remote resource at https://account.lab.fiware.org/oauth2/
        #   authorize?client_id=859680e0c8cb4c65b5d2d6fb99ef1595&redirect_uri=
        #   http://localhost:8000/oauth/complete/fiware/&state=eXpNpKJ5jqsZoOB
        #   cm0X1hLcmaSCNoa3E&response_type=code.
        #   (Reason: CORS header ‘Access-Control-Allow-Origin’ missing).
        return redirect(data)

    stock_data = _get_stock(access_token, request.user.username)
    if 'error' in stock_data:
        return JsonResponse(stock_data, safe=False)

    marketplace_ids = []
    for product in stock_data:
        marketplace_ids.append(_get_productid_from_specification(product))

    applications, error = Application.list(marketplace_ids)
    if error is not None:
        return JsonResponse({'error': error})

    data = []
    for product in stock_data:
        pid = _get_productid_from_specification(product)
        found = False
        for application in applications:
            if pid == application.marketplace_id:
                found = True
                break
        if not found:
            data.append(product)

    request.session['stock'] = data
    request.session.modified = True

    return JsonResponse(data, safe=False)


@login_required
def load_owned_applications(request):
    valid, data = sso.utils.get_token(request.user, request.get_full_path())
    if valid:
        access_token = data
    else:
        # FIXME: Cross-Origin Request Blocked: The Same Origin Policy disallows
        # reading the remote resource at https://account.lab.fiware.org/oauth2/
        #   authorize?client_id=859680e0c8cb4c65b5d2d6fb99ef1595&redirect_uri=
        #   http://localhost:8000/oauth/complete/fiware/&state=eXpNpKJ5jqsZoOB
        #   cm0X1hLcmaSCNoa3E&response_type=code.
        #   (Reason: CORS header ‘Access-Control-Allow-Origin’ missing).
        return redirect(data)

    stock_data = _get_stock(access_token, request.user.username)
    if 'error' in stock_data:
        return JsonResponse(stock_data, safe=False)

    marketplace_ids = []
    for product in stock_data:
        marketplace_ids.append(_get_productid_from_specification(product))

    applications = Application.list(marketplace_ids, return_dict=True)

    if 'error' not in applications or applications['error'] is None:
        request.session['owned_apps'] = applications['app_list']
        request.session.modified = True

    return JsonResponse(applications, safe=False)


@login_required
def load_applications(request):
    valid, data = sso.utils.get_token(request.user, request.get_full_path())
    if valid:
        access_token = data
    else:
        # FIXME: Cross-Origin Request Blocked: The Same Origin Policy disallows
        # reading the remote resource at https://account.lab.fiware.org/oauth2/
        #   authorize?client_id=859680e0c8cb4c65b5d2d6fb99ef1595&redirect_uri=
        #   http://localhost:8000/oauth/complete/fiware/&state=eXpNpKJ5jqsZoOB
        #   cm0X1hLcmaSCNoa3E&response_type=code.
        #   (Reason: CORS header ‘Access-Control-Allow-Origin’ missing).
        return redirect(data)

    stock_data = _get_stock(access_token, request.user.username)
    if 'error' in stock_data:
        return JsonResponse(stock_data, safe=False)
    inventory_data = _get_inventory(access_token, request.user.username)
    if 'error' in inventory_data:
        return JsonResponse(inventory_data, safe=False)

    marketplace_ids = []
    for product in stock_data:
        marketplace_ids.append(_get_productid_from_specification(product))
    for offering in inventory_data:
        marketplace_ids.append(
            _get_productid_from_offering(offering, access_token))

    applications = Application.list(marketplace_ids, return_dict=True)

    if 'error' not in applications or applications['error'] is None:
        request.session['applications'] = applications['app_list']
        request.session.modified = True

    return JsonResponse(applications, safe=False)


def _get_stock(access_token, username):
    headers = {"Authorization": "bearer " + access_token}
    url = settings.MARKETPLACE_URL + \
        "/DSProductCatalog/api/catalogManagement/v2/productSpecification" + \
        "?lifecycleStatus=Launched" + \
        "&relatedParty.id=" + username

    text_data = requests.request("GET", url, headers=headers).text
    return json.loads(text_data)


def _get_inventory(access_token, username):
    headers = {"Authorization": "bearer " + access_token}
    url = settings.MARKETPLACE_URL + \
        "/DSProductInventory/api/productInventory/v2/product" + \
        "?status=Active" + \
        "&relatedParty.id=" + username

    text_data = requests.request("GET", url, headers=headers).text
    return json.loads(text_data)


def _get_productid_from_specification(data):
    return data["id"]


def _get_productid_from_offering(data, access_token):
    headers = {"Authorization": "bearer " + access_token}
    url = data["productOffering"]['href']

    text_data = requests.request("GET", url, headers=headers).text
    json_data = json.loads(text_data)

    return json_data["productSpecification"]["id"]


@login_required
@permission_required('experimentstool.register_app')
def upload_application(request):
    if 'stock' not in request.session:
        return JsonResponse({'error': 'No stock products loaded'})

    products = request.session['stock']
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

    # TODO: check errors, if does not exist, etc.
    blueprint_package = request.FILES['blueprint_package']

    # save the package temporarily
    tmp_package_file = tempfile.NamedTemporaryFile()
    for chunk in blueprint_package.chunks():
        tmp_package_file.write(chunk)

    response = JsonResponse(Application.create(tmp_package_file.name,
                                               mso4sc_id,
                                               product_id,
                                               request.user,
                                               return_dict=True))
    tmp_package_file.close()

    return response


@login_required
def get_application_inputs(request):
    if 'applications' not in request.session:
        return JsonResponse({'error': 'No applications loaded'})

    application_index = int(request.GET.get('application_index', -1))

    if application_index < 0:
        return JsonResponse({'error': 'Bad application id provided'})

    application_id = request.session['applications'][application_index]["id"]

    return JsonResponse(Application.get_inputs(application_id,
                                               return_dict=True))


@login_required
@permission_required('experimentstool.remove_app')
def remove_application(request):
    if 'owned_apps' not in request.session:
        return JsonResponse({'error': 'No applications loaded'})

    application_index = int(request.GET.get('application_index', -1))

    if application_index < 0:
        return JsonResponse({'error': 'Bad application id provided'})

    application_id = request.session['owned_apps'][application_index]["id"]

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
@permission_required('experimentstool.run_instance')
def execute_deployment(request):
    deployment_id = int(request.POST.get('deployment_id', -1))
    workflow = request.POST.get('workflow')
    force = bool(request.POST.get('force', False))

    if deployment_id is None:
        return {'error': 'No deployment provided'}

    if deployment_id < 0:
        return {'error': 'Bad deployment provided'}

    return JsonResponse(
        WorkflowExecution.create(deployment_id,
                                 workflow,
                                 request.user,
                                 force=force,
                                 return_dict=True))


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

    if not reset and 'log_offset' in request.session:
        offset = request.session['log_offset']

    events, error = WorkflowExecution.get_execution_events(execution_pk,
                                                           offset,
                                                           request.user)
    if error is None:
        if offset != events['last']:
            request.session['log_offset'] = events.pop('last')
            request.session.modified = True

    return JsonResponse({'events': events, 'error': error})


@login_required
@permission_required('experimentstool.destroy_instance')
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
