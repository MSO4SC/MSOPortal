import logging

from django.conf import settings
from django.db import models

from django.forms.models import model_to_dict


# Get an instance of a logger
LOGGER = logging.getLogger(__name__)


def _to_dict(model_instance):
    if model_instance is None:
        return None
    else:
        return model_to_dict(model_instance)


class RemoteDesktopInfrastructure(models.Model):
    name = models.CharField(max_length=50)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    host = models.CharField(max_length=50)
    user = models.CharField(max_length=50)
    password = models.CharField(max_length=50)

    list_cmd = models.CharField(max_length=50)
    create_cmd = models.CharField(max_length=50)

    NOVNC = 'noVNC'
    RD_CHOICES = (
        (NOVNC, 'noVNC'),
    )
    rd_tool = models.CharField(
        max_length=5,
        choices=RD_CHOICES,
        default=NOVNC,
    )

    @classmethod
    def get(cls, pk, owner, return_dict=False):
        """ If returning a dict, password is removed """
        error = None
        rdi = None
        try:
            rdi = cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            pass

        if rdi is not None and owner != rdi.owner:
            rdi = None
            error = 'Remote desktop infra does not belong to user'

        if not return_dict:
            return (rdi, error)
        else:
            if rdi is not None:
                rdi = _to_dict(rdi)
                rdi.pop('password')
            return {'rdi': rdi, 'error': error}

    @classmethod
    def list(cls, owner, return_dict=False):
        """ If returning a dict, passwords are removed """
        error = None
        rdi_list = []
        try:
            rdi_list = cls.objects.filter(owner=owner)
        except cls.DoesNotExist:
            pass
        except Exception as err:
            LOGGER.exception(err)
            error = str(err)

        if not return_dict:
            return (rdi_list, error)
        else:
            passwordless_list = []
            for rdi in rdi_list:
                rdi_dict = _to_dict(rdi)
                rdi_dict.pop('password')
                passwordless_list.append(rdi_dict)
            return {'rdi_list':  passwordless_list,
                    'error': error}

    @classmethod
    def create(cls,
               name,
               owner,
               host,
               user,
               password,
               rdi_type,
               list_cmd,
               create_cmd,
               return_dict=False):
        error = None
        rdi = None
        try:
            rdi = cls.objects.create(name=name,
                                     owner=owner,
                                     host=host,
                                     user=user,
                                     password=password,
                                     rd_tool=rdi_type,
                                     list_cmd=list_cmd,
                                     create_cmd=create_cmd)
        except Exception as err:
            LOGGER.exception(err)
            error = str(err)

        if not return_dict:
            return (rdi, error)
        else:
            return {'rdi': _to_dict(rdi), 'error': error}

    @classmethod
    def remove(cls, pk, owner, return_dict=False):
        """ If returning a dict, passwords are removed """
        rdi, error = cls.get(pk, owner)

        if error is None:
            if rdi is not None:
                rdi.delete()
            else:
                error = "Can't delete Remote Desktop" +\
                    " Infra because it doesn't exists"

        if not return_dict:
            return (rdi, error)
        else:
            if rdi is not None:
                rdi = _to_dict(rdi)
                rdi.pop('password')
            return {'rdi': rdi, 'error': error}

    def __str__(self):
        return "{0}: Remote Desktop at {1} from {2}({3})".format(
            self.name,
            self.host,
            self.owner.username,
            self.user)
