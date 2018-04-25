import json
import time
import traceback
from urllib.parse import urlparse
from datetime import datetime

from django.conf import settings
from django.db import models

from django.forms.models import model_to_dict

from cloudify_rest_client import CloudifyClient
from cloudify_rest_client.executions import Execution
from cloudify_rest_client.exceptions import CloudifyClientError
from cloudify_rest_client.exceptions \
    import DeploymentEnvironmentCreationPendingError
from cloudify_rest_client.exceptions \
    import DeploymentEnvironmentCreationInProgressError

WAIT_FOR_EXECUTION_SLEEP_INTERVAL = 3


def _to_dict(model_instance):
    if model_instance is None:
        return None
    else:
        return model_to_dict(model_instance)


class Orchestrator(models.Model):
    """ Custom permissions for Experiments Tool app """

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
            ('deploy_instance',
             'Can install an instance in the orchestrator'),
            ('run_instance',
             'Can run jobs of an instance in the orchestrator'),
            ('undeploy_instance',
             'Can uninstall an install in the orchestrator'),
            ('destroy_instance',
             'Can delete an app instance in the orchestrator'),
        )


class HPCInfrastructure(models.Model):
    name = models.CharField(max_length=50)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    host = models.CharField(max_length=50)
    user = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    time_zone = models.CharField(max_length=20)

    SLURM = 'SLURM'
    MANAGER_CHOICES = (
        (SLURM, 'Slurm'),
    )
    manager = models.CharField(
        max_length=5,
        choices=MANAGER_CHOICES,
        default=SLURM,
    )

    @classmethod
    def get(cls, pk, owner, return_dict=False):
        error = None
        hpc = None
        try:
            hpc = cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            pass

        if (owner != hpc.owner):
            hpc = None
            error = 'HPC does not belong to user'

        if not return_dict:
            return (hpc, error)
        else:
            if hpc is not None:
                hpc = _to_dict(hpc)
            return {'hpc': hpc, 'error': error}

    @classmethod
    def list(cls, owner, return_dict=False):
        error = None
        hpc_list = []
        try:
            hpc_list = cls.objects.filter(owner=owner)
        except cls.DoesNotExist:
            pass
        except Exception as err:
            print(traceback.format_exc())
            error = str(err)

        if not return_dict:
            return (hpc_list, error)
        else:
            return {'hpc_list':  [_to_dict(hpc) for hpc in hpc_list],
                    'error': error}

    @classmethod
    def create(cls,
               name,
               owner,
               host,
               user,
               password,
               tz,
               manager,
               return_dict=False):
        error = None
        hpc = None
        try:
            hpc = cls.objects.create(name=name,
                                     owner=owner,
                                     host=host,
                                     user=user,
                                     password=password,
                                     time_zone=tz,
                                     manager=manager)
        except Exception as err:
            print(traceback.format_exc())
            error = str(err)

        if not return_dict:
            return (hpc, error)
        else:
            return {'hpc': _to_dict(hpc), 'error': error}

    @classmethod
    def remove(cls, pk, owner, return_dict=False):
        hpc, error = cls.get(pk, owner)

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
            self.user)

    def to_dict(self):
        return {
            'credentials': {
                'host': self.host,
                'user': self.user,
                'password': self.password,
            },
            'country_tz': self.time_zone,
            'workload_manager': self.manager
        }


def _get_client():
    client = CloudifyClient(host=settings.ORCHESTRATOR_HOST,
                            username=settings.ORCHESTRATOR_USER,
                            password=settings.ORCHESTRATOR_PASS,
                            tenant=settings.ORCHESTRATOR_TENANT)
    return client


class Application(models.Model):
    name = models.CharField(max_length=50)

    description = models.CharField(max_length=256, null=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    # TODO: Link to marketplace app

    @classmethod
    def get(cls, pk, owner, return_dict=False):
        error = None
        app = None
        try:
            app = cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            pass

        if (owner != app.owner):
            app = None
            error = 'Application does not belong to user'

        if not return_dict:
            return (app, error)
        else:
            if app is not None:
                app = _to_dict(app)
            return {'app': app, 'error': error}

    @classmethod
    def list(cls, owner, return_dict=False):
        error = None
        app_list = []
        try:
            app_list = cls.objects.filter(owner=owner)
        except cls.DoesNotExist:
            pass

        if not return_dict:
            return (app_list, error)
        else:
            return {'app_list': [_to_dict(app) for app in app_list],
                    'error': error}

    @classmethod
    def create(cls, path, blueprint_id, owner, return_dict=False):
        error = None
        app = None

        blueprint, error = cls._upload_blueprint(path, blueprint_id)

        if not error:
            try:
                print(blueprint['id'])
                app = cls.objects.create(
                    name=blueprint['id'],
                    description=blueprint['description'],
                    owner=owner)
            except Exception as err:
                print(traceback.format_exc())
                error = str(err)
                cls._remove_blueprint(blueprint['id'])

        if not return_dict:
            return (app, error)
        else:
            return {'app': _to_dict(app), 'error': error}

    @classmethod
    def get_inputs(cls, pk, owner, return_dict=False):
        """ Returns a list of dict with inputs, and a string error """
        inputs = None
        app, error = cls.get(pk, owner)

        if error is None:
            if app is not None:
                inputs, error = cls._get_inputs(app.name)
            else:
                error = "Can't get app inputs because it doesn't exists"

        if not return_dict:
            return (inputs, error)
        else:
            return {'inputs': inputs, 'error': error}

    @classmethod
    def remove(cls, pk, owner, return_dict=False):
        app, error = cls.get(pk, owner)

        if error is None:
            if app is not None:
                _, error = cls._remove_blueprint(app.name)
                if error is None:
                    app.delete()
            else:
                error = "Can't delete aplication because it doesn't exists"

        if not return_dict:
            return (app, error)
        else:
            return {'app': _to_dict(app), 'error': error}

    def __str__(self):
        return "Application {0} from {1}".format(
            self.name,
            self.owner.username)

    @staticmethod
    def _upload_blueprint(path, blueprint_id):
        error = None
        blueprint = None
        is_url = bool(urlparse(path).scheme)

        client = _get_client()
        try:
            if is_url:
                blueprint = client.blueprints.publish_archive(
                    path, blueprint_id)
            else:
                blueprint = client.blueprints.upload(path, blueprint_id)
        except CloudifyClientError as err:
            print(traceback.format_exc())
            error = str(err)

        return (blueprint, error)

    @staticmethod
    def _get_blueprints():
        error = None
        blueprints = None
        client = _get_client()
        try:
            blueprints = client.blueprints.list().items
        except CloudifyClientError as err:
            print(traceback.format_exc())
            error = str(err)

        return (blueprints, error)

    @staticmethod
    def _get_inputs(app_id):
        error = None
        data = None
        client = _get_client()
        try:
            blueprint_dict = client.blueprints.get(app_id)
            inputs = blueprint_dict['plan']['inputs']
            data = [{'name': name,
                     'type': input.get('type', '-'),
                     'default': input.get('default', '-'),
                     'description': input.get('description', '-')}
                    for name, input in inputs.items()]
        except CloudifyClientError as err:
            print(traceback.format_exc())
            error = str(err)

        return (data, error)

    @staticmethod
    def _remove_blueprint(app_id):
        error = None
        blueprint = None
        client = _get_client()
        try:
            blueprint = client.blueprints.delete(app_id)
        except CloudifyClientError as err:
            print(traceback.format_exc())
            error = str(err)

        return (blueprint, error)


class AppInstance(models.Model):
    name = models.CharField(max_length=50)
    app = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
    )

    description = models.CharField(max_length=256, null=True)
    inputs = models.CharField(max_length=256, null=True)
    outputs = models.CharField(max_length=256, null=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    @classmethod
    def get(cls, pk, owner, return_dict=False):
        error = None
        instance = None
        try:
            instance = cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            pass

        if (owner != instance.owner):
            instance = None
            error = 'Application instance does not belong to user'

        if not return_dict:
            return (instance, error)
        else:
            if instance is not None:
                instance = _to_dict(instance)
            return {'instance': instance, 'error': error}

    @classmethod
    def list(cls, owner, return_dict=False):
        error = None
        instance_list = []
        try:
            instance_list = cls.objects.filter(owner=owner)
        except cls.DoesNotExist:
            pass

        if not return_dict:
            return (instance_list, error)
        else:
            return {
                'instance_list': [_to_dict(inst) for inst in instance_list],
                'error': error}

    @classmethod
    def create(cls, app_pk, deployment_id, inputs, owner, return_dict=False):
        error = None
        instance = None

        app, error = Application.get(app_pk, owner)
        if error is None:
            if app is None:
                error = "Can't create instance because app doesn't exists"
            else:
                deployment, error = cls._create_deployment(app.name,
                                                           deployment_id,
                                                           inputs)

        if error is None:
            try:
                instance = cls.objects.create(
                    name=deployment['id'],
                    app=app,
                    description=deployment['description'],
                    inputs=json.dumps(
                        deployment['inputs'],
                        ensure_ascii=False,
                        separators=(',', ':')),
                    outputs=json.dumps(
                        deployment['outputs'],
                        ensure_ascii=False,
                        separators=(',', ':')),
                    owner=owner)
            except Exception as err:
                print(traceback.format_exc())
                error = str(err)
                cls._destroy_deployment(deployment['id'])

        if not return_dict:
            return (instance, error)
        else:
            return {'instance': _to_dict(instance), 'error': error}

    @classmethod
    def remove(cls, pk, owner, return_dict=False, force=False):
        instance, error = cls.get(pk, owner)

        if error is None:
            if instance is not None:
                _, error = cls._destroy_deployment(
                    instance.name,
                    force=force)
                if error is None:
                    instance.delete()
            else:
                error = "Can't delete instance because it doesn't exists"

        if not return_dict:
            return (instance, error)
        else:
            return {'instance': _to_dict(instance), 'error': error}

    def __str__(self):
        return "Instance {0}:{1} from {2}".format(
            self.app.name,
            self.name,
            self.owner.username)

    @classmethod
    def _create_deployment(cls, app_id, instance_id, inputs, retries=3):
        error = None
        deployment = None

        client = _get_client()
        try:
            deployment = client.deployments.create(
                app_id,
                instance_id,
                inputs=inputs,
                skip_plugins_validation=True
            )
        except (DeploymentEnvironmentCreationPendingError,
                DeploymentEnvironmentCreationInProgressError) as err:
            if (retries > 0):
                time.sleep(WAIT_FOR_EXECUTION_SLEEP_INTERVAL)
                deployment, error = cls._create_deployment(app_id,
                                                           instance_id,
                                                           inputs,
                                                           retries - 1)
            print(traceback.format_exc())
            error = str(err)
        except CloudifyClientError as err:
            print(traceback.format_exc())
            error = str(err)

        return (deployment, error)

    @staticmethod
    def _destroy_deployment(instance_id, force=False):
        error = None
        deployment = None
        client = _get_client()
        try:
            deployment = client.deployments.delete(
                instance_id, ignore_live_nodes=force)
        except CloudifyClientError as err:
            print(traceback.format_exc())
            error = str(err)

        return (deployment, error)

    def _install_deployment(self, force):
        return self._execute_workflow('install', force)

    def _run_deployment(self, force):
        return self._execute_workflow('run_jobs', force)

    def _uninstall_deployment(self, force):
        params = None
        if force:
            params = {'ignore_failure': True}
        return self._execute_workflow('uninstall', force, params=params)


class WorkflowExecution(models.Model):
    INSTALL = 'install'
    RUN = 'run_jobs'
    UNINSTALL = 'uninstall'
    DESTROY = 'destroy'

    id_code = models.CharField(max_length=50)
    app_instance = models.ForeignKey(
        AppInstance,
        on_delete=models.CASCADE,
    )
    workflow = models.CharField(max_length=50)
    # can't use auto_now_add because it set editable=False
    # and therefore model_to_dict skips the field
    created_on = models.DateTimeField(editable=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    @classmethod
    def get(cls, pk, owner, return_dict=False):
        error = None
        execution = None
        try:
            execution = cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            pass

        if (owner != execution.owner):
            execution = None
            error = 'Instance execution does not belong to user'

        if not return_dict:
            return (execution, error)
        else:
            if execution is not None:
                execution = _to_dict(execution)
            return {'execution': execution, 'error': error}

    @classmethod
    def list(cls, owner, return_dict=False):
        error = None
        execution_list = []
        try:
            execution_list = cls.objects.filter(owner=owner)
        except cls.DoesNotExist:
            pass

        if not return_dict:
            return (execution_list, error)
        else:
            return {
                'execution_list':
                    [_to_dict(execution) for execution in execution_list],
                'error': error}

    @classmethod
    def list_by_instance_workflow(cls,
                                  owner,
                                  instance,
                                  workflow,
                                  return_dict=False):
        error = None
        execution_list = []
        try:
            execution_list = cls.objects.filter(owner=owner,
                                                app_instance=instance,
                                                workflow=workflow)
        except cls.DoesNotExist:
            pass

        if not return_dict:
            return (execution_list, error)
        else:
            return {
                'execution_list':
                    [_to_dict(execution) for execution in execution_list],
                'error': error}

    @classmethod
    def create(cls, instance_pk, workflow, owner,
               force=False, params=None, return_dict=False):
        error = None
        execution = None

        instance, error = AppInstance.get(instance_pk, owner)
        if error is None:
            if instance is None:
                error = \
                    "Can't create execution because instance doesn't exists"
            else:
                execution, error = cls._execute_workflow(instance.name,
                                                         workflow,
                                                         force,
                                                         params)

        if error is None:
            try:
                execution = cls.objects.create(
                    id_code=execution['id'],
                    app_instance=instance,
                    workflow=workflow,
                    created_on=datetime.now(),
                    owner=owner)
            except Exception as err:
                print(traceback.format_exc())
                error = str(err)
                # TODO: cancel execution

        if not return_dict:
            return (execution, error)
        else:
            return {'execution': _to_dict(execution), 'error': error}

    def __str__(self):
        return "Instance {0}:{1} from {2}".format(
            self.app,
            self.instance_id,
            self.owner.username)

    @staticmethod
    def _execute_workflow(deployment_id, workflow, force, params=None):
        error = None
        execution = None

        client = _get_client()
        try:
            execution = client.executions.start(deployment_id,
                                                workflow,
                                                parameters=params,
                                                force=force)
        except CloudifyClientError as err:
            print(traceback.format_exc())
            error = str(err)

        return (execution, error)

    @classmethod
    def get_execution_events(cls, execution_pk, offset, owner,
                             return_dict=False):
        events = None
        wf_execution, error = cls.get(execution_pk, owner)
        if error is None:
            if wf_execution is None:
                error = \
                    "Can't get execution events because it doesn't exists"
            else:
                events = cls._get_execution_events(
                    wf_execution.id_code,
                    offset)

        if not return_dict:
            return (events, error)
        else:
            return {'events': events, 'error': error}

    @staticmethod
    def _get_execution_events(execution_id, offset):
        client = _get_client()

        execution = client.executions.get(execution_id)
        events = client.events.list(execution_id=execution_id,
                                    _offset=offset,
                                    _size=100)
        last_message = events.metadata.pagination.total

        return {
            'logs': WorkflowExecution._events_to_string(events.items),
            'last': last_message,
            'status': execution.status,
            'finished': WorkflowExecution._is_execution_finished(
                execution.status)
        }

    @staticmethod
    def _events_to_string(events):
        response = []
        for event in events:
            event_type = event["type"]
            message = ""
            if event_type == "cloudify_event":
                cloudify_event_type = event["event_type"]
                message = event["reported_timestamp"] + \
                    " " + event["message"]
                if cloudify_event_type == "workflow_node_event":
                    message += " " + event["node_instance_id"] + \
                        " (" + event["node_name"] + ")"
                elif cloudify_event_type == "sending_task" \
                        or cloudify_event_type == "task_started" \
                        or cloudify_event_type == "task_succeeded" \
                        or cloudify_event_type == "task_failed":
                    # message += " [" + event["operation"] + "]"
                    if event["node_instance_id"]:
                        message += " " + event["node_instance_id"]
                    if event["node_name"]:
                        message += " (" + event["node_name"] + ")"
                elif cloudify_event_type == "workflow_started" \
                        or cloudify_event_type == "workflow_succeeded" \
                        or cloudify_event_type == "workflow_failed" \
                        or cloudify_event_type == "workflow_cancelled":
                    pass
                else:
                    message = json.dumps(event)
                if event["error_causes"]:
                    for cause in event["error_causes"]:
                        message += "\n" + \
                            cause['type'] + ": " + cause["message"]
                        message += "\n\t" + cause["traceback"]
            else:
                message = json.dumps(event)
            response.append(message)

        return response

    @staticmethod
    def _is_execution_finished(status):
        return status in Execution.END_STATES
