from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.shortcuts import render
from django.http import JsonResponse
from django.forms.models import model_to_dict

from paramiko.ssh_exception import SSHException
from remotedesktops import ssh
from remotedesktops.models import RemoteDesktopInfrastructure


@login_required
def remotedesktops(request):
    return render(request, 'remotedesktops.html', {})


@login_required
def get_rdi_list(request):
    response = _get_rdi_list(request.user)
    if response:
        rdi_list = serializers.serialize(
            'json',
            response
        )
    else:
        rdi_list = []
    return JsonResponse(rdi_list, safe=False)


@login_required
def add_rdi(request):
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

    list_cmd = request.POST.get('list_cmd', None)
    if not list_cmd or list_cmd == '':
        return JsonResponse({'error': 'No list command provided'})

    create_cmd = request.POST.get('create_cmd', None)
    if not create_cmd or create_cmd == '':
        return JsonResponse({'error': 'No create command provided'})

    return JsonResponse(_add_rdi(name,
                                 request.user,
                                 host,
                                 user,
                                 password,
                                 RemoteDesktopInfrastructure.NOVNC,
                                 list_cmd,
                                 create_cmd)
                        )


@login_required
def delete_rdi(request):
    pk = request.POST.get('pk', None)
    if not pk or pk == '':
        # TODO validation
        return JsonResponse({'error':
                             'No remote desktop infrastructure provided'})

    return JsonResponse(_delete_rdi(request.user, pk))


@login_required
def get_rd_list(request):
    rdi_pk = request.POST.get('rdi_pk', -1)
    rdi = _get_remote_desktop_infrastructure(rdi_pk)
    if rdi is None:
        return JsonResponse({'error': 'Bad infrastructure provided'})

    return JsonResponse(_get_rd_list(rdi.host,
                                     rdi.user,
                                     rdi.password,
                                     rdi.list_cmd),
                        safe=False)


@login_required
def add_rd(request):
    rdi_pk = request.POST.get('rdi_pk', -1)
    rdi = _get_remote_desktop_infrastructure(rdi_pk)
    if rdi is None:
        return JsonResponse({'error': 'Bad infrastructure provided'})

    return JsonResponse(_add_rd(rdi.host,
                                rdi.user,
                                rdi.password,
                                rdi.create_cmd),
                        safe=False)


def _get_rdi_list(user):
    try:
        rdi_list = RemoteDesktopInfrastructure.objects.filter(
            owner=user)
    except RemoteDesktopInfrastructure.DoesNotExist:
        rdi_list = []
    return rdi_list


def _add_rdi(name, owner, host, user, password, tool, list_cmd, create_cmd):
    rdi = RemoteDesktopInfrastructure.objects.create(name=name,
                                                     owner=owner,
                                                     host=host,
                                                     user=user,
                                                     password=password,
                                                     rd_tool=tool,
                                                     list_cmd=list_cmd,
                                                     create_cmd=create_cmd)
    return {'rdi': model_to_dict(rdi)}


def _delete_rdi(owner, pk):
    rdi = _get_remote_desktop_infrastructure(pk)
    if not rdi:
        return {'error': 'Remote desktop infrastructure does not exists'}

    if (owner == rdi.owner):
        rdi.delete()
        return {'rdi': model_to_dict(rdi)}
    else:
        return {'error': 'Remote desktop infrastructure does not' +
                ' belong to user'}


def _get_remote_desktop_infrastructure(pk):
    try:
        rdi = RemoteDesktopInfrastructure.objects.get(pk=pk)
    except RemoteDesktopInfrastructure.DoesNotExist:
        rdi = None
    return rdi


def _get_rd_list(host, user, password, list_cmd):
    try:
        client = ssh.SshClient(host, user, password)
        output, exit_code = client.send_command(list_cmd, wait_result=True)
        client.close_connection()
        if exit_code is not 0:
            return {'error': 'Exit(' + str(exit_code) + '): ' + output}

    except SSHException as ssh_ex:
        return {'error': str(ssh_ex)}

    output_list = output.split('\n')
    output_list.pop()  # remove last empty line
    rd_list = []
    if len(output_list) > 1:
        for index in range(1, len(output_list), 2):
            rd_list.append({'url': output_list[index],
                            'ro_url': output_list[index + 1][10:]})

    return {'rd_list': rd_list}


def _add_rd(host, user, password, create_cmd):
    try:
        client = ssh.SshClient(host, user, password)
        output, exit_code = client.send_command(create_cmd, wait_result=True)
        client.close_connection()
        if exit_code is not 0:
            return {'error': "Couldn't create a new desktop"}
    except SSHException as ssh_ex:
        return {'error': str(ssh_ex)}

    return {}
