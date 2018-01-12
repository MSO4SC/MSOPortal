from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.shortcuts import render
from django.http import JsonResponse
from django.forms.models import model_to_dict

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
def get_rd_list(request):
    rdi_pk = request.POST.get('rdi_pk', -1)
    rdi = _get_remote_desktop_infrastructure(rdi_pk)
    if rdi is None:
        return JsonResponse({'error': 'Bad '})

    return


def _get_rdi_list(user):
    try:
        rdi_list = RemoteDesktopInfrastructure.objects.filter(
            owner=user)
    except RemoteDesktopInfrastructure.DoesNotExist:
        rdi_list = []
    return rdi_list


def _get_rd_list(host, user, password):
    # TODO: not implemented
    return []


def _add_rdi(name, owner, host, user, password, tool):
    rdi = RemoteDesktopInfrastructure.objects.create(name=name,
                                                     owner=owner,
                                                     host=host,
                                                     user=user,
                                                     password=password,
                                                     rd_tool=tool)
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
