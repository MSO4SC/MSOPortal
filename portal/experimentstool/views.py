""" Experiments Tool views module """

import datetime
import json
import tempfile
from typing import Dict, List
from urllib.parse import urlparse

import requests
import yaml
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import render

import sso
from experimentstool.models import (AppInstance, Application,
                                    ComputingInfrastructure, ComputingInstance,
                                    DataCatalogueKey)
from portal import settings
from sso.utils import token_required


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

    inputs_str = request.POST.get('inputs', None)
    if not inputs_str or inputs_str == '':
        # TODO validation
        return JsonResponse({'error': 'No inputs provided'})

    infra, error = ComputingInfrastructure.get(infra_pk)
    if error is not None:
        return JsonResponse({'error': error})

    definition = yaml.load(infra.definition)
    inputs_values = json.loads(inputs_str)
    processed_inputs, error = _process_inputs(definition, inputs_values)

    if error is not None:
        return JsonResponse({'error': error})
    return JsonResponse(
        ComputingInstance.create(
            name,
            request.user,
            infra_pk,
            yaml.dump(processed_inputs),
            return_dict=True))


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
    
    infra_config = None
    user_config = None
    data = None
    error = None
    if data_type == 'infra':
        infra, error = ComputingInfrastructure.get(pk)
        if error is None:
            data, error = infra.get_inputs_list()
    else: # app
        app, error = Application.get(pk)
        if error is None:
            data, error = app.get_inputs_list()
    
    if error is None:
        infra_config, error = _get_infra_config(request.user)
        user_config = _get_user_config(request.user)

    return JsonResponse({
        'inputs': data,
        'infra_config': infra_config,
        'user_config': user_config,
        'error': error})


def _get_infra_config(owner, secrets=False):
    infra_list, error = ComputingInstance.list(owner)
    if error is None:
        infra_config = {}
        for item in infra_list:
            key = item.infrastructure.infra_type.lower()+'_list'
            if key in infra_config:
                infra_config[key].append(item.to_dict(secrets=secrets))
            else:
                infra_config[key] = [item.to_dict(secrets=secrets)]
    return (infra_config, error)


def _get_user_config(owner):
    ckan_entrypoint = settings.DATACATALOGUE_URL
    ckan_key = DataCatalogueKey.get(owner)
    user_config = {
        'storage_list': [{
            'type': 'ckan',
            'config': {
                'entrypoint': ckan_entrypoint,
                'key': ckan_key.code
            }
        }]
    }
    if ckan_key is not None:
        user_config['storage_list'][0]['config']['key'] = ckan_key.code


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
    storage_str = request.POST.get('storage', "{}")
    storage = json.loads(storage_str)

    if (storage['type'] != "ckan"):
        return JsonResponse({"error": "Storage type '"+storage['type']+"' not supported"})

    datasets, error = _get_ckan_datasets(storage)

    names = []
    for dataset in datasets:
        names.append(dataset["name"])

    request.session['datasets'] = datasets
    request.session.modified = True

    return JsonResponse({'names': names, 'error': error})

def _get_ckan_datasets(storage):
    url = storage['config']['entrypoint'] + \
        "/api/3/action/package_search"

    key = storage['config']['key']

    datasets = []
    left = True
    offset = 0
    error = None
    while error is None and left:
        datasets_chunk, left, error = \
            _get_ckan_datasets_offset(url, key, offset)
        datasets += datasets_chunk
        offset += len(datasets_chunk)

    return (datasets, error)

def _get_ckan_datasets_offset(url, key, offset):
    datasets = []
    left = False
    error = None

    url += "?start="+str(offset)

    headers = {}
    if key is not None:
        headers = {'Authorization': key}
        url += "&include_private=True"

    text_data = requests.request("GET", url, headers=headers).text
    json_data = json.loads(text_data)
    if 'success' not in json_data or not bool(json_data["success"]):
        error = "Could not get datasets: "+text_data

    if error is None:
        if "result" in json_data and "results" in json_data["result"]:
            datasets = json_data["result"]["results"]
        else:
            error = "Could not get datasets: No results"

    if error is None:
        left = (int(json_data["result"]["count"]) - offset + len(datasets)) > 0

    return (datasets, left, error)


@login_required
def get_dataset_info(request):
    if 'datasets' not in request.session:
        return JsonResponse({'error': 'No datasets loaded'})

    datasets = request.session['datasets']
    dataset_index = int(request.POST.get('dataset', -1))

    if dataset_index >= len(datasets) or dataset_index < 0:
        return JsonResponse({'error': 'Bad dataset index provided'})

    return JsonResponse(datasets[dataset_index], safe=False)


def _replace_tag(path, infra_config, user_config, instance_config, dependencies):
    value = None
    error = None
    postpone = False
    keys = path.split('.')
    if keys[0] == 'INFRA_CONFIG':
        value = infra_config
    elif keys[0] == 'USER_CONFIG':
        value = user_config
    elif keys[0] == 'INSTANCE_CONFIG':
        value = instance_config
    else:
        if keys[0] in dependencies:
            value = dependencies[keys[0]]
        else:
            postpone = True

    if not postpone:
        for key in keys[1:]:
            if isinstance(value, Dict):
                if key in value:
                    value = value[key]
                else:
                    error = path+" does not exist in " + keys[0]
                    break
            elif isinstance(value, List):
                if len(value) > int(key):
                    value = value[int(key)]
                else:
                    error = "List in path "+path+" does not have enough items"
                    break
            else:
                # Data is not completely ready yet, postponing
                postpone = True
                break

    return (value, postpone, error)

def _get_input_value(
        input_id,
        input_def,
        inputs_values,
        infra_config,
        user_config,
        instance_config,
        dependencies,
        parent_key=''):
    if isinstance(input_def, Dict):
        if 'INPUT' in input_def:
            data = input_def['INPUT']
            if data['type'] == "list":
                choices = data['choices']
                postpone = False
                error = None
                if 'REPLACE' in data['choices']:
                    choices, postpone, error = _replace_tag(
                        data['choices']['REPLACE'],
                        infra_config,
                        user_config,
                        instance_config,
                        dependencies)
                if error is not None:
                    return (None, False, error)
                elif postpone:
                    return (None, True, None)
                else:
                    return (
                        choices[int(inputs_values[parent_key+'.'+input_id])],
                        False,
                        None)
            elif data['type'] == "resource_list" or data['type'] == "dataset_list":
                storage_def = {**data['storage']}
                postpone = False
                error = None
                if 'REPLACE' in storage_def:
                    storage_def, postpone, error = _replace_tag(
                        data['storage']['REPLACE'],
                        infra_config,
                        user_config,
                        instance_config,
                        dependencies)
                if error is not None:
                    return (None, False, error)
                elif postpone:
                    return (None, True, None)
                else:
                    if (storage_def['type'].upper() != "CKAN"):
                        return (
                            None,
                            False,
                            "Storage type '"+storage_def['type']+"' not supported")
                    datasets, error = _get_ckan_datasets(storage_def)
                    dataset = datasets[int(inputs_values[parent_key+'.'+input_id])]
                    storage = {**storage_def}
                    storage['dataset'] = _to_ascii(dataset)
                    if data['type'] == "resource_list":
                        if int(dataset["num_resources"]) > 0:
                            storage['resource'] = \
                                dataset['resources']\
                                    [int(inputs_values\
                                        [parent_key+'.'+input_id+":resource"])]
                        else:
                            return (
                                None,
                                False,
                                "Dataset "+dataset['name']+" does not have resources")
                    return (storage, False, None)
            elif data['type'] == "file" or data['type'] == "string":
                return (inputs_values[parent_key+'.'+input_id], False, None)
            elif data['type'] == "bool":
                return (bool(inputs_values[parent_key+'.'+input_id]), False, None)
            elif data['type'] == "int":
                return (int(inputs_values[parent_key+'.'+input_id]), False, None)
            elif data['type'] == "float":
                return (float(inputs_values[parent_key+'.'+input_id]), False, None)
            else:
                return (None, False, "Type '"+data['type']+"' not supported")
        elif 'REPLACE' in input_def:
            return _replace_tag(
                input_def['REPLACE'],
                infra_config,
                user_config,
                instance_config,
                dependencies)
        else:
            # recursive iteration over the dictionary
            value = {}
            need_reprocessing = False
            for key, data in input_def.items():
                value_data, postpone, error = _get_input_value(
                    key,
                    data,
                    inputs_values,
                    infra_config,
                    user_config,
                    instance_config,
                    dependencies,
                    parent_key=parent_key+'.'+input_id)
                if error is not None:
                    break
                need_reprocessing = need_reprocessing or postpone
                value[key] = value_data
            return (value, need_reprocessing, error)
    elif isinstance(input_def, List):
        # recursive iteration over the list
        value = []
        need_reprocessing = False
        for index, data in enumerate(input_def):
            value_data, postpone, error = _get_input_value(
                str(index),
                data,
                inputs_values,
                infra_config,
                user_config,
                instance_config,
                dependencies,
                parent_key=parent_key+'.'+input_id)
            if error is not None:
                break
            need_reprocessing = need_reprocessing or postpone
            value.append(value_data)
        return (value, need_reprocessing, error)
    else:
        return (input_def, False, None) # This is not managed by the portal, leave as it is

def _to_ascii(data):
    if isinstance(data, Dict):
        escaped_dict = {}
        for key, value in data.items():
            escaped_dict[key] = _to_ascii(value)
        return escaped_dict
    elif isinstance(data, List):
        escaped_list = []
        for item in data:
            escaped_list.append(_to_ascii(item))
        return escaped_list
    elif isinstance(data, str):
        return data.encode('ascii', 'ignore').decode('ascii')
    else:
        return data

def _process_inputs(
        definition,
        inputs_values,
        infra_config=None,
        user_config=None,
        instance_config=None):
    processed_inputs = {}
    error = None

    to_process = {**definition}
    condition = True
    while condition:
        postponed = {}
        for input_id, input_def in to_process.items():
            value, postpone, error = _get_input_value(
                input_id,
                input_def,
                inputs_values,
                infra_config,
                user_config,
                instance_config,
                processed_inputs)
            if error is not None:
                break
            if postpone:
                postponed[input_id] = input_def
            processed_inputs[input_id] = value
        condition = error is None and len(postponed) < len(to_process) and postponed
        to_process = {**postponed}

    if error is None and len(processed_inputs) != len(definition):
        error = "Dependency loop, couldn't process inputs"

    return (processed_inputs, error)


@login_required
@permission_required('experimentstool.create_instance')
def create_deployment(request):
    deployment_id = request.POST.get('deployment_id', None)
    application_id = int(request.POST.get('application_id', -1))
    inputs_str = request.POST.get('deployment_inputs', "{}")

    if not deployment_id or deployment_id is '':
        return JsonResponse({'error': 'No instance name provided'})
    if application_id < 0:
        return JsonResponse({'error': 'No application selected'})

    inputs_values = json.loads(inputs_str)
    definition, error = Application.get_inputs_definition(application_id)
    if error is not None:
        return JsonResponse({'error': error})

    infra_config, error = _get_infra_config(request.user, secrets=True)
    user_config = _get_user_config(request.user)
    instance_config = {
        "id": deployment_id + "_" + \
            datetime.datetime.now().strftime("%y%m%dT%H%M%S")
    }
    processed_inputs, error = _process_inputs(
        definition,
        inputs_values,
        infra_config,
        user_config,
        instance_config)
    
    if error is not None:
        return JsonResponse({'error': error})

    # print(yaml.dump(processed_inputs))  # FIXME remove
    instance, error = AppInstance.create(
        application_id,
        deployment_id,
        processed_inputs,
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
        error = instance.execute()

    return JsonResponse({
        "instance": instance.name,
        "error": error
    })

@login_required
def get_status(request):
    instance_pk = int(request.GET.get('instance_id', -1))
    offset = 0

    if instance_pk < 0:
        return JsonResponse({'error': 'Bad instance provided'})

    status, finished, error = \
        AppInstance.get_status(instance_pk, request.user)

    return JsonResponse({
        'finished': finished,
        'status': status,
        'error': error})

@login_required
def get_progress(request):
    instance_pk = int(request.GET.get('instance_id', -1))
    reset = request.GET.get("reset", "False") in ["True", "true", "TRUE"]

    if instance_pk < 0:
        return JsonResponse({'error': 'Bad instance provided'})

    workflow_status, progress, running_jobs, finished_jobs, finished, status, error = \
        AppInstance.get_progress(instance_pk, request.user)

    return JsonResponse({
        'workflow_status': workflow_status,
        'progress': progress,
        'running_jobs': running_jobs,
        'finished_jobs': finished_jobs,
        'finished': finished,
        'status': status,
        'error': error})


@login_required
def get_executions_events(request):
    instance_pk = int(request.GET.get('instance_id', -1))
    reset = request.GET.get("reset", "False") in ["True", "true", "TRUE"]

    if instance_pk < 0:
        return JsonResponse({'error': 'Bad instance provided'})

    events, error = AppInstance.get_instance_events(instance_pk,
                                                    request.user)

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
