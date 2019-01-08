""" Custom permissions """

from django.db import models


class Orchestrator(models.Model):
    """ Orchestrator Custom permissions """

    class Meta:

        managed = False  # No database table creation or deletion operations \
        # will be performed for this model.

        permissions = (
            ('register_app',
             'Can register a new app in the orchestrator'),
            ('remove_app',
             'Can remove an app in the orchestrator'),
            ('create_instance',
             'Can create a new app instance in the orchestrator'),
            ('run_instance',
             'Can run workflows of an instance in the orchestrator'),
            ('destroy_instance',
             'Can delete an app instance in the orchestrator'),
        )
