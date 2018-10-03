
import logging

from django.conf import settings
from django.db import models

from .common import _to_dict

# Get an instance of a logger
LOGGER = logging.getLogger(__name__)


class TunnelConnection(models.Model):
    """ Tunnel credentials """
    name = models.CharField(max_length=50)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    host = models.CharField(max_length=50)
    user = models.CharField(max_length=50)
    private_key = models.CharField(max_length=1800, blank=True, default='')
    private_key_password = models.CharField(
        max_length=50, blank=True, default='')
    password = models.CharField(max_length=50, blank=True, default='')

    @classmethod
    def get(cls, pkey, owner, return_dict=False):
        """ If returning a dict, password is removed """
        error = None
        tunnel = None
        try:
            tunnel = cls.objects.get(pk=pkey)
        except cls.DoesNotExist:
            pass

        if tunnel is not None and owner != tunnel.owner:
            tunnel = None
            error = 'Tunnel does not belong to user'

        if not return_dict:
            return (tunnel, error)
        else:
            if tunnel is not None:
                tunnel = _to_dict(tunnel)
                tunnel.pop('private_key')
                tunnel.pop('private_key_password')
                tunnel.pop('password')
            return {'tunnel': tunnel, 'error': error}

    @classmethod
    def list(cls, owner, return_dict=False):
        """ If returning a dict, passwords are removed """
        error = None
        tunnel_list = []
        try:
            tunnel_list = cls.objects.filter(owner=owner)
        except cls.DoesNotExist:
            pass
        except Exception as err:
            LOGGER.exception(err)
            error = str(err)

        if not return_dict:
            return (tunnel_list, error)
        else:
            passwordless_list = []
            for tunnel in tunnel_list:
                tunnel_dict = _to_dict(tunnel)
                tunnel_dict.pop('private_key')
                tunnel_dict.pop('private_key_password')
                tunnel_dict.pop('password')
                passwordless_list.append(tunnel_dict)
            return {'tunnel_list':  passwordless_list,
                    'error': error}

    @classmethod
    def create(cls,
               name,
               owner,
               host,
               user,
               private_key,
               private_key_password,
               password,
               return_dict=False):
        error = None
        tunnel = None
        try:
            tunnel = cls.objects.create(name=name,
                                        owner=owner,
                                        host=host,
                                        user=user,
                                        private_key=private_key,
                                        private_key_password=private_key_password,
                                        password=password)
        except Exception as err:
            LOGGER.exception(err)
            error = str(err)

        if not return_dict:
            return (tunnel, error)
        else:
            return {'tunnel': _to_dict(tunnel), 'error': error}

    @classmethod
    def remove(cls, pk, owner, return_dict=False):
        tunnel, error = cls.get(pk, owner)

        if error is None:
            if tunnel is not None:
                tunnel.delete()
            else:
                error = "Can't delete tunnel because it doesn't exists"

        if not return_dict:
            return (tunnel, error)
        else:
            if tunnel is not None:
                tunnel = _to_dict(tunnel)
                tunnel.pop('private_key')
                tunnel.pop('private_key_password')
                tunnel.pop('password')
            return {'tunnel': tunnel, 'error': error}

    def __str__(self):
        return "{0}: Tunnel at {1} from {2}({3})".format(
            self.name,
            self.host,
            self.owner.username,
            self.user)

    def to_dict(self):
        return {
            'host': self.host,
            'user': self.user,
            'private_key': self.private_key,
            'private_key_password': self.private_key_password,
            'password': self.password,
        }
