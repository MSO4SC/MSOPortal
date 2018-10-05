""" HPC models """
import logging

from django.conf import settings
from django.db import models
from django.db.utils import IntegrityError

from .common import _to_dict
from .connection import TunnelConnection

# Get an instance of a logger
LOGGER = logging.getLogger(__name__)


class HPCInfrastructure(models.Model):
    """ General HPC settings """
    name = models.CharField(max_length=50, unique=True)
    about_url = models.CharField(max_length=250)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    host = models.CharField(max_length=50)

    time_zone = models.CharField(max_length=20)

    SLURM = 'SLURM'
    TORQUE = 'TORQUE'
    MANAGER_CHOICES = (
        (SLURM, 'Slurm'),
        (TORQUE, 'Torque'),
    )
    manager = models.CharField(
        max_length=5,
        choices=MANAGER_CHOICES,
        default=SLURM,
    )

    @classmethod
    def _get(cls, pkey, return_dict=False):
        """ If returning a dict, password is removed """
        hpc = None
        try:
            hpc = cls.objects.get(pk=pkey)
        except cls.DoesNotExist:
            pass

        return hpc

    @classmethod
    def get(cls, pkey, owner, return_dict=False):
        """ If returning a dict, password is removed """
        error = None
        hpc = cls._get(pkey)

        if hpc is not None and owner != hpc.owner:
            hpc = None
            error = 'HPC does not belong to user'

        if not return_dict:
            return (hpc, error)
        else:
            return {'hpc': _to_dict(hpc), 'error': error}

    @classmethod
    def list(cls, owner, return_dict=False):
        error = None
        hpc_list = []
        try:
            hpc_list = cls.objects.filter(owner=owner)
        except cls.DoesNotExist:
            pass
        except Exception as err:
            LOGGER.exception(err)
            error = str(err)

        if not return_dict:
            return (hpc_list, error)
        else:
            return {'hpc_list': [_to_dict(hpc) for hpc in hpc_list],
                    'error': error}

    @classmethod
    def list_all(cls, owner, return_dict=False):
        error = None
        hpc_list = []
        try:
            hpc_list = cls.objects.all()
        except cls.DoesNotExist:
            pass
        except Exception as err:
            LOGGER.exception(err)
            error = str(err)

        if not return_dict:
            return (hpc_list, error)
        else:
            hpc_list_owned = []
            if hpc_list is not None:
                for hpc in hpc_list:
                    hpc_dict = _to_dict(hpc)
                    if hpc.owner == owner:
                        hpc_dict['owned'] = True
                    else:
                        hpc_dict['owned'] = False
                    hpc_list_owned.append(hpc_dict)
            return {'hpc_list': hpc_list_owned,
                    'error': error}

    @classmethod
    def create(cls,
               name,
               owner,
               about_url,
               host,
               tz,
               manager,
               return_dict=False):
        error = None
        hpc = None

        try:
            hpc = cls.objects.create(
                name=name,
                owner=owner,
                about_url=about_url,
                host=host,
                time_zone=tz,
                manager=manager)
        except IntegrityError as err:
            LOGGER.exception(err)
            error = "Can't create two HPC definitions with the same name."
        except Exception as err:
            LOGGER.exception(err)
            error = str(err)

        if not return_dict:
            return (hpc, error)
        else:
            return {'hpc': _to_dict(hpc), 'error': error}

    @classmethod
    def remove(cls, pkey, owner, return_dict=False):
        hpc, error = cls.get(pkey, owner)

        if error is None:
            if hpc is not None:
                hpc.delete()
            else:
                error = "Can't delete HPC because it doesn't exists"

        if not return_dict:
            return (hpc, error)
        else:
            return {'hpc': _to_dict(hpc), 'error': error}

    def __str__(self):
        return "{0}: HPC at {1} from {2}({3})".format(
            self.name,
            self.host,
            self.owner.username,
            self.manager)

    def to_dict(self):
        inputs_data = {
            'credentials': {
                'host': self.host
            },
            'country_tz': self.time_zone,
            'workload_manager': self.manager
        }

        if self.tunnel is not None:
            inputs_data['credentials']["tunnel"] = self.tunnel.to_dict()

        return inputs_data


class HPCInstance(models.Model):
    """ User's HPC """
    name = models.CharField(max_length=50)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    infrastructure = models.ForeignKey(
        HPCInfrastructure,
        on_delete=models.CASCADE,
        null=False
    )

    user = models.CharField(max_length=50)
    private_key = models.CharField(max_length=1800, blank=True, default='')
    private_key_password = models.CharField(
        max_length=50, blank=True, default='')
    password = models.CharField(max_length=50, blank=True, default='')
    tunnel = models.ForeignKey(
        TunnelConnection,
        on_delete=models.CASCADE,
        null=True
    )

    @classmethod
    def get(cls, pkey, owner, return_dict=False):
        """ If returning a dict, password is removed """
        error = None
        hpc = None
        try:
            hpc = cls.objects.get(pk=pkey)
        except cls.DoesNotExist:
            pass

        if hpc is not None and owner != hpc.owner:
            hpc = None
            error = 'HPC does not belong to user'

        if not return_dict:
            return (hpc, error)
        else:
            if hpc is not None:
                hpc_dict = _to_dict(hpc)
                hpc_dict.pop('private_key')
                hpc_dict.pop('private_key_password')
                hpc_dict.pop('password')
                hpc_dict["infrastructure"] = hpc.infrastructure.name
                if hpc.tunnel is not None:
                    hpc_dict['tunnel'] = _to_dict(hpc.tunnel)
                    hpc_dict['tunnel'].pop('private_key')
                    hpc_dict['tunnel'].pop('private_key_password')
                    hpc_dict['tunnel'].pop('password')
            return {'hpc': hpc_dict, 'error': error}

    @classmethod
    def list(cls, owner, return_dict=False):
        """ If returning a dict, passwords are removed """
        error = None
        hpc_list = []
        try:
            hpc_list = cls.objects.filter(owner=owner)
        except cls.DoesNotExist:
            pass
        except Exception as err:
            LOGGER.exception(err)
            error = str(err)

        if not return_dict:
            return (hpc_list, error)
        else:
            passwordless_list = []
            for hpc in hpc_list:
                hpc_dict = _to_dict(hpc)
                hpc_dict.pop('private_key')
                hpc_dict.pop('private_key_password')
                hpc_dict.pop('password')
                hpc_dict["infrastructure"] = hpc.infrastructure.name
                if hpc.tunnel is not None:
                    hpc_dict['tunnel'] = _to_dict(hpc.tunnel)
                    hpc_dict['tunnel'].pop('private_key')
                    hpc_dict['tunnel'].pop('private_key_password')
                    hpc_dict['tunnel'].pop('password')
                passwordless_list.append(hpc_dict)
            return {'hpc_list':  passwordless_list,
                    'error': error}

    @classmethod
    def create(cls,
               name,
               owner,
               infra_pk,
               user,
               private_key,
               private_key_password,
               password,
               tunnel_pk,
               return_dict=False):
        error = None
        hpc_infra = None
        hpc = None
        tunnel = None

        hpc_infra = HPCInfrastructure._get(infra_pk)
        if error is None and hpc_infra is None:
            error = "Can't create HPC because infrastructure doesn't exists"

        if error is None and tunnel_pk is not None:
            tunnel, error = TunnelConnection.get(tunnel_pk, owner)
            if error is None and tunnel is None:
                error = "Can't create HPC because tunnel doesn't exists"

        if error is None:
            try:
                hpc = cls.objects.create(name=name,
                                         owner=owner,
                                         infrastructure=hpc_infra,
                                         user=user,
                                         private_key=private_key,
                                         private_key_password=private_key_password,
                                         password=password,
                                         tunnel=tunnel)
            except Exception as err:
                LOGGER.exception(err)
                error = str(err)

        if not return_dict:
            return (hpc, error)
        else:
            hpc_dict = {}
            if hpc is not None:
                hpc_dict = _to_dict(hpc)
                hpc_dict.pop('private_key')
                hpc_dict.pop('private_key_password')
                hpc_dict.pop('password')
                hpc_dict["infrastructure"] = hpc.infrastructure.name
                if hpc.tunnel is not None:
                    hpc_dict['tunnel'] = _to_dict(hpc.tunnel)
                    hpc_dict['tunnel'].pop('private_key')
                    hpc_dict['tunnel'].pop('private_key_password')
                    hpc_dict['tunnel'].pop('password')
            return {'hpc': hpc_dict, 'error': error}

    @classmethod
    def remove(cls, pkey, owner, return_dict=False):
        hpc, error = cls.get(pkey, owner)

        if error is None:
            if hpc is not None:
                hpc.delete()
            else:
                error = "Can't delete HPC because it doesn't exists"

        if not return_dict:
            return (hpc, error)
        else:
            hpc_dict = {}
            if hpc is not None:
                hpc_dict = _to_dict(hpc)
                hpc_dict.pop('private_key')
                hpc_dict.pop('private_key_password')
                hpc_dict.pop('password')
                hpc_dict["infrastructure"] = hpc.infrastructure.name
                if hpc.tunnel is not None:
                    hpc_dict['tunnel'] = _to_dict(hpc.tunnel)
                    hpc_dict['tunnel'].pop('private_key')
                    hpc_dict['tunnel'].pop('private_key_password')
                    hpc_dict['tunnel'].pop('password')
            return {'hpc': hpc_dict, 'error': error}

    def __str__(self):
        return "{0}: {1} HPC from {2}({3})".format(
            self.name,
            self.infrastructure.name,
            self.owner.username,
            self.user)

    def to_dict(self):  # TODO: Implement
        inputs_data = {
            'credentials': {
                'host': self.host,
                'user': self.user,
                'private_key': self.private_key,
                'private_key_password': self.private_key_password,
                'password': self.password,
            },
            'country_tz': self.time_zone,
            'workload_manager': self.manager
        }

        if self.tunnel is not None:
            inputs_data['credentials']["tunnel"] = self.tunnel.to_dict()

        return inputs_data
