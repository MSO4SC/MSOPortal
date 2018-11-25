""" General infrastructure models """
import logging
import yaml

from typing import Dict, List

from django.conf import settings
from django.db import models
from django.db.utils import IntegrityError

from .common import _to_dict, get_inputs_list, delete_secrets, NAME_TAG, ORDER_TAG

# Get an instance of a logger
LOGGER = logging.getLogger(__name__)


class ComputingInfrastructure(models.Model):
    """ General Infrastructure settings """
    name = models.CharField(max_length=50, unique=True)
    about_url = models.CharField(max_length=250)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    HPC = 'HPC'
    OPENSTACK = 'OPENSTACK'
    EOSC = 'EOSC'
    TYPE_CHOICES = (
        (HPC, 'HPC'),
        (OPENSTACK, 'OpenStack'),
        (EOSC, 'EOSC-Hub')
    )
    infra_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES
    )

    SLURM = 'SLURM'
    TORQUE = 'TORQUE'
    BASH = 'BASH'
    MANAGER_CHOICES = (
        (SLURM, 'Slurm'),
        (TORQUE, 'Torque'),
        (BASH, 'Bash')
    )
    manager = models.CharField(
        max_length=5,
        choices=MANAGER_CHOICES
    )

    definition = models.TextField()

    @classmethod
    def get(cls, pkey, owner=None, return_dict=False):
        """ If owner is not specified, it is ignored """
        error = None
        infra = None
        try:
            infra = cls.objects.get(pk=pkey)
        except cls.DoesNotExist:
            pass

        if owner is not None:
            if infra is not None and owner != infra.owner:
                infra = None
                error = 'HPC does not belong to user'

        if not return_dict:
            return (infra, error)
        else:
            return {'infra': _to_dict(infra), 'error': error}

    @classmethod
    def list(cls, owner, return_dict=False):
        error = None
        infra_list = []
        try:
            infra_list = cls.objects.filter(owner=owner)
        except cls.DoesNotExist:
            pass
        except Exception as err:
            LOGGER.exception(err)
            error = str(err)

        if not return_dict:
            return (infra_list, error)
        else:
            return {'infra_list': [_to_dict(infra) for infra in infra_list],
                    'error': error}

    @classmethod
    def list_all(cls, owner, return_dict=False):
        error = None
        infra_list = []
        try:
            infra_list = cls.objects.all()
        except cls.DoesNotExist:
            pass
        except Exception as err:
            LOGGER.exception(err)
            error = str(err)

        if not return_dict:
            return (infra_list, error)
        else:
            infra_list_owned = []
            if infra_list is not None:
                for infra in infra_list:
                    infra_dict = _to_dict(infra)
                    if infra.owner == owner:
                        infra_dict['owned'] = True
                    else:
                        infra_dict['owned'] = False
                    infra_list_owned.append(infra_dict)
            return {'infra_list': infra_list_owned,
                    'error': error}

    @classmethod
    def create(cls,
               name,
               owner,
               about_url,
               infra_type,
               manager,
               definition,
               return_dict=False):
        error = None
        infra = None

        # validate definition structure according to type
        try:
            dict_def = yaml.load(definition)
        except yaml.YAMLError as err:
            error = "Couldn't parse definition into a valid YAML:" + str(err)

        if error is None:
            if 'wm_config' not in dict_def:
                error = '"wm_config" key not found in definition file'
            elif infra_type == cls.HPC:
                if 'country_tz' not in dict_def['wm_config']:
                    error = '"country_tz" key not found in definition file under "wm_config"'
                elif 'partitions' not in dict_def:
                    error = '"partitions" key not found in definition file'
                elif not isinstance(dict_def['partitions'], List) \
                        and dict_def['partitions'] != 'None':
                    error = '"partitions" key does not define a list or "None" value'
                elif 'mpi_versions' not in dict_def:
                    error = '"mpi_versions" key not found in definition file'
                elif not isinstance(dict_def['mpi_versions'], List) \
                        and dict_def['mpi_versions'] != 'None':
                    error = '"mpi_versions" key does not define a list or "None" value'
                elif 'singularity_versions' not in dict_def:
                    error = '"singularity_versions" key not found in definition file'
                elif not isinstance(dict_def['singularity_versions'], List) \
                        and dict_def['singularity_versions'] != 'None':
                    error = '"singularity_versions" key does not define a list or "None" value'
            elif infra_type == cls.OPENSTACK:
                if 'openstack_config' not in dict_def:
                    error = '"openstack_config" key not found in definition file'
                elif not isinstance(dict_def['openstack_config'], Dict):
                    error = '"openstack_config" key does not define a dictionary'
                elif 'openstack_flavors' not in dict_def:
                    error = '"openstack_flavors" key not found in definition file'
                elif not isinstance(dict_def['openstack_flavors'], List) \
                        and dict_def['openstack_flavors'] != 'None':
                    error = '"openstack_flavors" key does not define a list or "None" value'
                elif 'openstack_images' not in dict_def:
                    error = '"openstack_images" key not found in definition file'
                elif not isinstance(dict_def['openstack_images'], List) \
                        and dict_def['openstack_images'] != 'None':
                    error = '"openstack_images" key does not define a list or "None" value'
                elif 'openstack_networks' not in dict_def:
                    error = '"openstack_networks" key not found in definition file'
                elif not isinstance(dict_def['openstack_networks'], List) \
                        and dict_def['openstack_networks'] != 'None':
                    error = '"openstack_networks" key does not define a list or "None" value'
                elif 'openstack_volumes' not in dict_def:
                    error = '"openstack_volumes" key not found in definition file'
                elif not isinstance(dict_def['openstack_volumes'], List) \
                        and dict_def['openstack_volumes'] != 'None':
                    error = '"openstack_volumes" key does not define a list or "None" value'
            elif infra_type == cls.EOSC:
                if 'eosc_config' not in dict_def:
                    error = '"eosc_config" key not found in definition file'
                elif not isinstance(dict_def['eosc_config'], Dict):
                    error = '"eosc_config" key does not define a dictionary'
                elif 'eosc_flavors' not in dict_def:
                    error = '"eosc_flavors" key not found in definition file'
                elif not isinstance(dict_def['eosc_flavors'], List) \
                        and dict_def['eosc_flavors'] != 'None':
                    error = '"eosc_flavors" key does not define a list or "None" value'
                elif 'eosc_images' not in dict_def:
                    error = '"eosc_images" key not found in definition file'
                elif not isinstance(dict_def['eosc_images'], List) \
                        and dict_def['eosc_images'] != 'None':
                    error = '"eosc_images" key does not define a list or "None" value'
                elif 'eosc_networks' not in dict_def:
                    error = '"eosc_networks" key not found in definition file'
                elif not isinstance(dict_def['eosc_networks'], List) \
                        and dict_def['eosc_networks'] != 'None':
                    error = '"eosc_networks" key does not define a list or "None" value'
                elif 'eosc_volumes' not in dict_def:
                    error = '"eosc_volumes" key not found in definition file'
                elif not isinstance(dict_def['eosc_volumes'], List) \
                        and dict_def['eosc_volumes'] != 'None':
                    error = '"eosc_volumes" key does not define a list or "None" value'
            else:
                error = 'unsopported type: "'+infra_type+'"'

        if error is None:
            try:
                infra = cls.objects.create(
                    name=name,
                    owner=owner,
                    about_url=about_url,
                    infra_type=infra_type,
                    manager=manager,
                    definition=definition)
            except IntegrityError as err:
                error = "Can't create two HPC definitions with the same name."
            except Exception as err:
                error = str(err)

        if error is not None:
            LOGGER.exception(error)

        if not return_dict:
            return (infra, error)
        else:
            return {'infra': _to_dict(infra), 'error': error}

    @classmethod
    def remove(cls, pkey, owner, return_dict=False):
        infra, error = cls.get(pkey, owner)

        if error is None:
            if infra is not None:
                infra.delete()
            else:
                error = "Can't delete infrastructure because it doesn't exists"

        if not return_dict:
            return (infra, error)
        else:
            return {'infra': _to_dict(infra), 'error': error}

    def get_inputs_list(self):
        # TODO results of this method could be saved
        #   only when definition chages
        return (get_inputs_list(yaml.load(self.definition)), None)

    def __str__(self):
        return "{0}: {1} from {2}({3})".format(
            self.name,
            self.infra_type,
            self.owner.username,
            self.manager)


class ComputingInstance(models.Model):
    """ User's Infrastructure """
    name = models.CharField(max_length=50)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    infrastructure = models.ForeignKey(
        ComputingInfrastructure,
        on_delete=models.CASCADE,
        null=False
    )

    definition = models.TextField()

    @classmethod
    def get(cls, pkey, owner, return_dict=False):
        """ If returning a dict, secrets are removed """
        error = None
        computing = None
        try:
            computing = cls.objects.get(pk=pkey)
        except cls.DoesNotExist:
            pass

        if computing is not None and owner != computing.owner:
            computing = None
            error = 'HPC does not belong to user'

        if not return_dict:
            return (computing, error)
        else:
            return {'computing': computing.to_dict() if computing is not None else None,
                    'error': error}

    @classmethod
    def list(cls, owner, return_dict=False):
        error = None
        computing_list = []
        try:
            computing_list = cls.objects.filter(owner=owner)
        except cls.DoesNotExist:
            pass
        except Exception as err:
            LOGGER.exception(err)
            error = str(err)

        if not return_dict:
            return (computing_list, error)
        else:
            return {
                'computing_list':  [computing.to_dict() for computing in computing_list],
                'error': error}

    @classmethod
    def create(cls,
               name,
               owner,
               infra_pk,
               definition,
               return_dict=False):
        error = None
        infra = None
        computing = None

        if error is None:
            infra, error = ComputingInfrastructure.get(infra_pk)
            if error is None and infra is None:
                error = "Can't create HPC because infrastructure doesn't exists"

        if error is None:
            try:
                yaml.load(definition)
            except yaml.YAMLError as err:
                error = "Couldn't parse definition into a valid YAML:" + \
                    str(err)

        if error is None:
            try:
                computing = cls.objects.create(name=name,
                                               owner=owner,
                                               infrastructure=infra,
                                               definition=definition)
            except Exception as err:
                error = str(err)

        if error is not None:
            LOGGER.exception(err)

        if not return_dict:
            return (computing, error)
        else:
            return {'computing': computing.to_dict() if computing is not None else None,
                    'error': error}

    @classmethod
    def remove(cls, pkey, owner, return_dict=False):
        computing, error = cls.get(pkey, owner)

        if error is None:
            if computing is not None:
                computing.delete()
            else:
                error = "Can't delete HPC because it doesn't exists"

        if not return_dict:
            return (computing, error)
        else:
            return {'computing': computing.to_dict() if computing is not None else None,
                    'error': error}

    def __str__(self):
        return "{0}: {1} HPC from {2}({3})".format(
            self.name,
            self.infrastructure.name,
            self.owner.username,
            self.user)

    def to_dict(self, secrets=False):
        computing_dict: Dict = {}
        dict_def: Dict = {}

        computing_dict = _to_dict(self)
        if not secrets:
            computing_dict['definition'] = \
                delete_secrets(
                    yaml.load(self.infrastructure.definition),
                    yaml.load(self.definition))
        else:
            computing_dict['definition'] = \
                yaml.load(self.definition)
        if computing_dict['definition']['wm_config'] is None:
            computing_dict['definition']['wm_config'] = {}
        computing_dict['definition']['wm_config']['workload_manager'] = \
            self.infrastructure.manager
        computing_dict["infrastructure"] = \
            self.infrastructure.name + \
            " ("+self.infrastructure.infra_type+")"

        return computing_dict
