""" Experiments Tool views module """

import re
import json
import yaml
import time
import tempfile
from urllib.parse import urlparse
import requests

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.http import JsonResponse

import sso
from sso.utils import token_required
from portal import settings

from experimentstool.models import (Application,
                                    AppInstance,
                                    WorkflowExecution,
                                    ComputingInfrastructure,
                                    ComputingInstance,
                                    TunnelConnection,
                                    DataCatalogueKey)


@login_required
def experimentstool(request):
    context = {
        'datacatalogue_url': settings.DATACATALOGUE_URL,
        'marketplace_url': settings.MARKETPLACE_URL,
    }

    return render(request, 'experimentstool.html', context)


@login_required
def get_ckan_key(request):
    return JsonResponse(
        DataCatalogueKey.get(request.user, return_dict=True),
        safe=False)


@login_required
def update_ckan_key(request):
    code = request.POST.get('ckan_key', None)
    if code is None:
        return JsonResponse({'error': "No key provided"})

    key = DataCatalogueKey.get(request.user)

    if code == '' and key is not None:
        return JsonResponse(
            DataCatalogueKey.remove(request.user,
                                    return_dict=True),
            safe=False)

    if key is None:
        return JsonResponse(
            DataCatalogueKey.create(code,
                                    request.user,
                                    return_dict=True),
            safe=False)
    else:
        DataCatalogueKey.objects.filter()
        key.update(code=code)
        return JsonResponse(
            {'key': code, 'error': None}
        )


@login_required
def get_owned_infra_list(request):
    return JsonResponse(
        ComputingInfrastructure.list(request.user, return_dict=True),
        safe=False)


@login_required
def get_infra_list(request):
    return JsonResponse(
        ComputingInfrastructure.list_all(request.user, return_dict=True),
        safe=False)


@login_required
def get_computing_list(request):
    return JsonResponse(
        ComputingInstance.list(request.user, return_dict=True),
        safe=False)


@login_required
def add_infra(request):
    name = request.POST.get('name', None)
    if not name or name == '':
        # TODO validation
        return JsonResponse({'error': 'No name provided'})
    
    about_url = request.POST.get('about', None)
    if not about_url or about_url == '':
        # TODO validation
        return JsonResponse({'error': 'No about url provided'})

    infra_type = request.POST.get('infra_type', None)
    if not infra_type or infra_type == '':
        # TODO validation
        return JsonResponse({'error': 'No type provided'})

    manager = request.POST.get('manager', None)
    if not manager or manager == '':
        # TODO validation
        return JsonResponse({'error': 'No workload manager provided'})

    definition = ''
    if "definition" in request.FILES:
        definition = str(request.FILES['definition'].read(), "utf-8")

    return JsonResponse(
        ComputingInfrastructure.create(
            name,
            request.user,
            about_url,
            infra_type,
            manager,
            definition,
            return_dict=True))


@login_required
def add_computing(request):
    infra_pk = request.POST.get('infra', None)
    if not infra_pk or infra_pk == '':
        # TODO validation
        return JsonResponse({'error': 'No computing infrastructure provided'})

    name = request.POST.get('name', None)
    if not name or name == '':
        # TODO validation
        return JsonResponse({'error': 'No name provided'})

    json_inputs = request.POST.get('inputs', None)
    if not json_inputs or json_inputs == '':
        # TODO validation
        return JsonResponse({'error': 'No inputs provided'})

    infra, error = ComputingInfrastructure.get(infra_pk)
    if error is not None:
        return JsonResponse({'error': error})

    # TODO check validity (null)
    definition = yaml.load(infra.definition)
    inputs = json.loads(json_inputs)
    for path, value in inputs.items():
        keys = path[1:].split('.')
        definition = _update_input(definition, keys, value)
    yaml_definition = yaml.dump(definition)

    return JsonResponse(
        ComputingInstance.create(
            name,
            request.user,
            infra_pk,
            yaml_definition,
            return_dict=True))


def _update_input(definition, keys, value):
    response = definition

    #Check if the key references a list
    try:
        key = int(keys[0])
    except ValueError:
        key = str(keys[0])

    if len(keys) > 1:
        response[key] = _update_input(definition[key], keys[1:], value)
    else:
        config = definition[key]['INPUT']
        if config['type'] == 'string' \
                or config['type'] == 'file':
            response[key] = str(value)
        elif config['type'] == 'int':
            response[key] = int(value)
        elif config['type'] == 'float':
            response[key] = float(value)
        elif config['type'] == 'bool':
            response[key] = bool(value)
        else:
            response[key] = value # lists
    return response

@login_required
def delete_infra(request):
    pk = request.POST.get('pk', None)
    if not pk or pk == '':
        # TODO validation
        return JsonResponse({'error': 'No computing provided'})

    return JsonResponse(
        ComputingInfrastructure.remove(
            pk,
            request.user,
            return_dict=True))


@login_required
def delete_computing(request):
    pk = request.POST.get('pk', None)
    if not pk or pk == '':
        # TODO validation
        return JsonResponse({'error': 'No computing provided'})

    return JsonResponse(
        ComputingInstance.remove(
            pk,
            request.user,
            return_dict=True))


@login_required
def get_inputs(request):
    data_type = request.POST.get('type', None)
    if data_type != 'infra' and data_type != 'app':
        # TODO validation
        return JsonResponse({'error': 'No valid type "'+data_type+'" provided'})
    pk = request.POST.get('pk', None)
    if not pk or pk == '':
        # TODO validation
        return JsonResponse({'error': 'No valid object provided'})
    
    data = None
    error = None
    if data_type == 'infra':
        infra, error = ComputingInfrastructure.get(pk)
        if error is None:
            data = infra.get_inputs_list()
    else: # app
        app, error = ComputingInfrastructure.get(pk) # TODO: app
        if error is None:
            data = app.get_inputs_list()

    return JsonResponse({'inputs': data, 'error': error})


@login_required
def get_tunnel_list(request):
    return JsonResponse(
        TunnelConnection.list(request.user, return_dict=True),
        safe=False)


@login_required
def add_tunnel(request):
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

    key = str(request.FILES['key'].read(), "utf-8")
    key_password = request.POST.get('key_password', '')
    password = request.POST.get('password', '')
    if key == '' and password == '':
        return JsonResponse({'error': 'No authentication (key/password) provided'})

    return JsonResponse(
        TunnelConnection.create(name,
                                request.user,
                                host,
                                user,
                                key,
                                key_password,
                                password,
                                return_dict=True))


@login_required
def delete_tunnel(request):
    pk = request.POST.get('pk', None)
    if not pk or pk == '':
        # TODO validation
        return JsonResponse({'error': 'No computing provided'})

    return JsonResponse(
        ComputingInstance.remove(
            pk,
            request.user,
            return_dict=True))


@token_required
def get_new_stock(request, *args, **kwargs):
    access_token = kwargs['token']
    if not access_token:
        return JsonResponse({'redirect': kwargs['url']+'/experimentstool/'})
    uid = sso.utils.get_uid(request.user)

    stock_data = _get_stock(access_token, uid)
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


@token_required
def load_owned_applications(request, *args, **kwargs):
    access_token = kwargs['token']
    if not access_token:
        return JsonResponse({'redirect': kwargs['url']+'/experimentstool/'})

    applications = Application.list_owned(request.user, return_dict=True)

    return JsonResponse(applications, safe=False)


@token_required
def load_applications(request, *args, **kwargs):
    access_token = kwargs['token']
    if not access_token:
        return JsonResponse({'redirect': kwargs['url']+'/experimentstool/'})
    uid = sso.utils.get_uid(request.user)

    stock_data = _get_stock(access_token, uid)
    if 'error' in stock_data:
        return JsonResponse(stock_data, safe=False)
    inventory_data = _get_inventory(access_token, uid)
    if 'error' in inventory_data:
        return JsonResponse(inventory_data, safe=False)

    marketplace_ids = ['-1'] # id for apps that are not in the marketplace
    for product in stock_data:
        marketplace_ids.append(_get_productid_from_specification(product))
    for offering in inventory_data:
        marketplace_ids.append(
            _get_productid_from_offering(offering, access_token))

    applications = Application.list(marketplace_ids, return_dict=True)

    return JsonResponse(applications, safe=False)


def _get_stock(access_token, uid):
    headers = {"Authorization": "bearer " + access_token}
    url = settings.MARKETPLACE_URL + \
        "/DSProductCatalog/api/catalogManagement/v2/productSpecification" + \
        "?lifecycleStatus=Launched" + \
        "&relatedParty.id=" + uid

    text_data = requests.request("GET", url, headers=headers).text
    return json.loads(text_data)


def _get_inventory(access_token, uid):
    headers = {"Authorization": "bearer " + access_token}
    url = settings.MARKETPLACE_URL + \
        "/DSProductInventory/api/productInventory/v2/product" + \
        "?status=Active" + \
        "&relatedParty.id=" + uid

    text_data = requests.request("GET", url, headers=headers).text
    return json.loads(text_data)


def _get_productid_from_specification(data):
    return data["id"]


def _get_productid_from_offering(data, access_token):
    headers = {"Authorization": "bearer " + access_token}
    url = settings.MARKETPLACE_URL + \
        urlparse(data["productOffering"]['href']).path

    text_data = requests.request("GET", url, headers=headers).text
    json_data = json.loads(text_data)

    return json_data["productSpecification"]["id"]


@login_required
@permission_required('experimentstool.register_app')
def upload_application(request):
    product_id = request.POST.get('product', None)
    if not product_id:
        return JsonResponse({'error': 'No product id provided'})

    mso4sc_id = request.POST.get('mso_id', None)
    if not mso4sc_id or mso4sc_id == '':
        # TODO validation
        return JsonResponse({'error': 'No mso4sc id provided'})

    register_for_all = product_id == "-1"
    if register_for_all:
        pass
    elif 'stock' in request.session:
        products = request.session['stock']
        product = None
        for _p in products:
            if _p["id"] == product_id:
                product = _p
                break
        if not product:
            return JsonResponse({'error': 'Product not found'})
    else:
        return JsonResponse({'error': 'No stock products loaded'})

    # TODO: check errors, if does not exist, etc.
    blueprint_package = request.FILES['blueprint_package']

    # save the package temporarily
    tmp_package_file = tempfile.NamedTemporaryFile(
        suffix=".tar.gz", delete=False)
    for chunk in blueprint_package.chunks():
        tmp_package_file.write(chunk)
    tmp_package_file.flush()

    response = JsonResponse(Application.create(tmp_package_file.name,
                                               mso4sc_id,
                                               product_id,
                                               request.user,
                                               return_dict=True))
    tmp_package_file.close()

    return response


@login_required
def get_application_inputs(request):
    application_id = int(request.GET.get('application_id', -1))

    if application_id < 0:
        return JsonResponse({'error': 'Bad application id provided'})

    return JsonResponse(Application.get_inputs(application_id,
                                               return_dict=True))


@login_required
@permission_required('experimentstool.remove_app')
def remove_application(request):
    application_id = int(request.GET.get('application_id', -1))

    if application_id < 0:
        return JsonResponse({'error': 'Bad application id provided'})

    return JsonResponse(Application.remove(application_id,
                                           request.user,
                                           return_dict=True))


@login_required
def get_datasets(request):
    url = settings.DATACATALOGUE_URL + \
        "/api/3/action/package_search"

    key = DataCatalogueKey.get(request.user)

    names = []
    datasets = []
    left = True
    offset = 0
    error = None
    while error is None and left:
        names_chunk, datasets_chunk, left, error = \
            _get_datasets(url, key, offset)
        names += names_chunk
        datasets += datasets_chunk
        offset += len(names_chunk)

    request.session['datasets'] = datasets
    request.session.modified = True

    return JsonResponse({'names': names, 'error': error})


def _get_datasets(url, key, offset):
    datasets = []
    names = []
    left = False
    error = None

    url += "?start="+str(offset)

    headers = {}
    if key is not None:
        headers = {'Authorization': key.code}
        url += "&include_private=True"

    text_data = requests.request("GET", url, headers=headers).text
    json_data = json.loads(text_data)
    if 'success' not in json_data or not bool(json_data["success"]):
        error = "Could not get datasets: "+text_data

    if error is None:
        if "result" in json_data and "results" in json_data["result"]:
            datasets = json_data["result"]["results"]
            for dataset in json_data["result"]["results"]:
                names.append(dataset["name"])
        else:
            error = "Could not get datasets: No results"

    if error is None:
        left = (int(json_data["result"]["count"]) - offset + len(names)) > 0

    return (names, datasets, left, error)


@login_required
def get_dataset_info(request):
    if 'datasets' not in request.session:
        return JsonResponse({'error': 'No datasets loaded'})

    datasets = request.session['datasets']
    dataset_index = int(request.POST.get('dataset', -1))

    if dataset_index >= len(datasets) or dataset_index < 0:
        return JsonResponse({'error': 'Bad dataset index provided'})

    return JsonResponse(datasets[dataset_index], safe=False)


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

    computing_list, error = ComputingInstance.list(request.user)
    if error is not None:
        return JsonResponse({'error': error})

    ckan_key_code = ""
    key = DataCatalogueKey.get(request.user)
    if key is not None:
        ckan_key_code = key.code

    computing_pattern = re.compile('^mso4sc_computing_(.)*$')
    dataset_pattern = re.compile('^mso4sc_dataset_(.)*$')
    dataset_resource_pattern = re.compile('^resource_mso4sc_dataset_(.)*$')
    outputdataset_pattern = re.compile('^mso4sc_outdataset_(.)*$')
    datacatalogue_pattern = re.compile('^mso4sc_datacatalogue_(.)*$')
    tosca_inputs = {}
    for _input, value in inputs.items():
        if computing_pattern.match(_input):
            computing_pk = value
            if computing_pk < 0:
                # the computing input has no configuration
                tosca_inputs[_input] = {}
                continue

            computing = None
            for computing_item in computing_list:
                if computing_item.id == computing_pk:
                    computing = computing_item
                    break
            if not computing:
                return JsonResponse({'error': 'Bad HPC provided. Please ' +
                                     'refresh and try again'})

            tosca_inputs[_input] = computing.to_dict()
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
            dataset = datasets[dataset_index]
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
        elif outputdataset_pattern.match(_input):
            if 'datasets' not in request.session:
                return JsonResponse({'error': 'No datasets loaded'})
            datasets = request.session['datasets']

            # get the dataset
            dataset_index = value
            if dataset_index >= len(datasets) or dataset_index < 0:
                # the dataset input has no configuration
                tosca_inputs[_input] = ""
                continue
            dataset = datasets[dataset_index]
            if 'error' in dataset:
                return JsonResponse(dataset)

            tosca_inputs[_input] = dataset["id"]
        elif datacatalogue_pattern.match(_input):
            ckan_value = ""
            if _input.endswith("entrypoint"):
                ckan_value = settings.DATACATALOGUE_URL
            elif _input.endswith("key"):
                ckan_value = ckan_key_code

            tosca_inputs[_input] = ckan_value
        else:
            tosca_inputs[_input] = value

    instance, error = AppInstance.create(application_id,
                                         deployment_id,
                                         tosca_inputs,
                                         request.user)

    return JsonResponse({
        "instance": instance.name if instance is not None else None,
        "error": error
    })


@login_required
def get_deployments(request):
    return JsonResponse(
        AppInstance.list(request.user, return_dict=True),
        safe=False)


@login_required
@permission_required('experimentstool.run_instance')
def execute_deployment(request):
    deployment_id = int(request.POST.get('deployment_id', -1))

    if deployment_id is None:
        return {'error': 'No deployment provided'}

    if deployment_id < 0:
        return {'error': 'Bad deployment provided'}

    instance, error = AppInstance.get(deployment_id, request.user)
    if error is None:
        error = instance.reset_execution(request.user)
        time.sleep(1)
        if error is None:
            instance.run_workflows(request.user)

    return JsonResponse({
        "instance": instance.name,
        "error": error
    })


@login_required
def get_executions_events(request):
    instance_pk = int(request.GET.get('instance_id', -1))
    reset = request.GET.get("reset", "False") in ["True", "true", "TRUE"]
    offset = 0

    if instance_pk < 0:
        return JsonResponse({'error': 'Bad instance provided'})

    if not reset and 'log_offset' in request.session:
        offset = request.session['log_offset']

    events, error = AppInstance.get_instance_events(instance_pk,
                                                    offset,
                                                    request.user)
    if error is None:
        if offset != events['last'] or \
                ('log_offset' in request.session and
                 offset != request.session['log_offset']):
            request.session['log_offset'] = events.pop('last')
            request.session.modified = True

    return JsonResponse({'events': events, 'error': error})


@login_required
def get_runjobs_workflowid(request):
    instance_pk = int(request.GET.get('instance_id', -1))

    if instance_pk < 0:
        return JsonResponse({'error': 'Bad instance provided'})

    return JsonResponse(AppInstance.get_instance_runjobs_workflowid(
        instance_pk,
        request.user,
        return_dict=True))


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
