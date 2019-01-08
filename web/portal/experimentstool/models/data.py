""" Data models """

import logging

from django.conf import settings
from django.db import models

from .common import _to_dict

# Get an instance of a logger
LOGGER = logging.getLogger(__name__)


class DataCatalogueKey(models.Model):
    """ Data catalogue key model """
    code = models.CharField(max_length=50)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    @classmethod
    def get(cls, owner, return_dict=False):
        """ If returning a dict, password is removed """
        key = None
        try:
            key = cls.objects.get(owner=owner)
        except cls.DoesNotExist:
            pass

        if not return_dict:
            return key
        else:
            if key is not None:
                key = _to_dict(key)
            return {'key': key}

    @classmethod
    def create(cls,
               code,
               owner,
               return_dict=False):
        """ Creates a new key in the database, for a concrete user """
        error = None
        key = None
        try:
            key = cls.objects.create(code=code, owner=owner)
        except Exception as err:
            LOGGER.exception(err)
            error = str(err)

        if not return_dict:
            return (key, error)
        else:
            return {'key': _to_dict(key), 'error': error}

    def update(self,
               code):
        """ Update the key value in the dtabase """
        self.code = code
        self.save()

    @classmethod
    def remove(cls, owner, return_dict=False):
        """ Removes the owner's key from database """
        error = None
        key = cls.get(owner)

        if key is not None:
            key.delete()
        else:
            error = "Can't delete key because it doesn't exists"

        if not return_dict:
            return (key, error)
        else:
            return {'key': _to_dict(key), 'error': error}

    def __str__(self):
        return "Key from {0}".format(self.owner.username)
