""" Application models """

import time
import json
import logging
from urllib.parse import urlparse
import yaml

from django.conf import settings

from django.db import models, connection, IntegrityError
from django.utils import timezone

from cloudify_rest_client import CloudifyClient
from cloudify_rest_client.executions import Execution
from cloudify_rest_client.exceptions import (
    DeploymentEnvironmentCreationPendingError,
    DeploymentEnvironmentCreationInProgressError,
    CloudifyClientError)

from .common import backend, _to_dict, get_inputs_list, delete_secrets, NAME_TAG, ORDER_TAG

# Get an instance of a logger
LOGGER = logging.getLogger(__name__)

WAIT_FOR_EXECUTION_SLEEP_INTERVAL = 5


def _get_client():
    client = CloudifyClient(host=settings.ORCHESTRATOR_HOST,
                            username=settings.ORCHESTRATOR_USER,
                            password=settings.ORCHESTRATOR_PASS,
                            tenant=settings.ORCHESTRATOR_TENANT)
    return client


class Application(models.Model):
    name = models.CharField(max_length=50, unique=True)

    description = models.CharField(max_length=256, null=True)
    marketplace_id = models.CharField(max_length=10, db_index=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    job_nodes = models.PositiveIntegerField(default=0)
    job_instances = models.PositiveIntegerField(default=0)

    @classmethod
    def _get(cls, pk):
        app = None
        try:
            app = cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            pass

        return app

    @classmethod
    def get(cls, pk, owner=None, return_dict=False):
        error = None
        app = cls._get(pk)

        if owner is not None and app is not None and owner != app.owner:
            app = None
            error = 'Application does not belong to user'

        if not return_dict:
            return (app, error)
        else:
            if app is not None:
                app = _to_dict(app)
            return {'app': app, 'error': error}

    @classmethod
    def list(cls, marketplace_ids, return_dict=False):
        error = None
        app_list = []
        try:
            app_list = cls.objects.filter(marketplace_id__in=marketplace_ids)
        except cls.DoesNotExist:
            pass

        if not return_dict:
            return (app_list, error)
        else:
            return {'app_list': [_to_dict(app) for app in app_list],
                    'error': error}

    @classmethod
    def list_owned(cls, owner, return_dict=False):
        error = None
        app_list = []
        try:
            app_list = cls.objects.filter(owner=owner)
        except cls.DoesNotExist:
            pass
        except Exception as err:
            LOGGER.exception(err)
            error = str(err)

        if not return_dict:
            return (app_list, error)
        else:
            return {'app_list': [_to_dict(app) for app in app_list],
                    'error': error}

    @classmethod
    def create(cls,
               path,
               blueprint_id,
               marketplace_id,
               owner,
               return_dict=False):
        error = None
        app = None

        blueprint, error = cls._upload_blueprint(path, blueprint_id)

        if not error:

            # get progress information
            job_nodes = 0
            job_instances = 0
            for node in blueprint['plan']['nodes']:
                if 'hpc.nodes.job' in node['type_hierarchy']:
                    job_nodes += 1
                if 'scale' in node['properties']:
                    job_instances += node['properties']['scale']
                else:
                    job_instances += 1

            try:
                app = cls.objects.create(
                    name=blueprint['id'],
                    description=blueprint['description'],
                    marketplace_id=marketplace_id,
                    owner=owner,
                    job_nodes=job_nodes,
                    job_instances=job_instances)
            except Exception as err:
                LOGGER.exception(err)
                error = str(err)
                cls._remove_blueprint(blueprint['id'])

        if not return_dict:
            return (app, error)
        else:
            return {'app': _to_dict(app), 'error': error}

    @classmethod
    def get_inputs(cls, pk, return_dict=False):
        """ Returns a list of dict with application inputs, and a string error """
        inputs = None
        app = cls._get(pk)

        if app is not None:
            inputs, error = app._get_inputs()
        else:
            error = "Can't get app inputs because it doesn't exists"

        if not return_dict:
            return (inputs, error)
        else:
            return {'inputs': inputs, 'error': error}
    
    def get_inputs_list(self):
        """ Returns an ordered list of inputs to be rendered """
        # TODO results of this method could be saved
        #   only when definition chages
        data = None
        definition, error = self._get_inputs_definition()
        if error is None:
            data = get_inputs_list(definition)
        
        return (data, error)
    
    @classmethod
    def get_inputs_definition(cls, pk, return_dict=False):
        app = cls._get(pk)
        definition = None

        if app is not None:
            definition, error = app._get_inputs_definition()
        else:
            error = "Can't get app inputs because it doesn't exists"        
        
        if not return_dict:
            return (definition, error)
        else:
            return {'definition': definition, 'error': error}

    @classmethod
    def remove(cls, pk, owner, return_dict=False):
        app, error = cls.get(pk, owner)

        if error is None:
            if app is not None:
                _, error = app._remove_blueprint()
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
        is_archive = bool(urlparse(path).scheme) or path.endswith(".tar.gz")

        client = _get_client()
        try:
            if is_archive:
                blueprint = client.blueprints.publish_archive(
                    path, blueprint_id)
            else:
                blueprint = client.blueprints.upload(path, blueprint_id)
        except CloudifyClientError as err:
            LOGGER.exception(err)
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
            LOGGER.exception(err)
            error = str(err)

        return (blueprints, error)

    def _get_inputs(self):
        error = None
        data = None
        client = _get_client()
        try:
            blueprint_dict = client.blueprints.get(self.name)
            inputs = blueprint_dict['plan']['inputs']
            # file = open("testfile.txt", "w")
            # import yaml
            # file.write(yaml.dump(blueprint_dict))
            # file.close()
            data = [{'name': name,
                     'type': input.get('type', '-'),
                     'default': input.get('default', '-'),
                     'description': input.get('description', '-')}
                    for name, input in inputs.items()]
        except CloudifyClientError as err:
            LOGGER.exception(err)
            error = str(err)

        return (data, error)
    
    def _get_inputs_definition(self):
        definition = None
        inputs, error = self._get_inputs()
        if error is None:
            definition = {}
            for item in inputs:
                definition[item['name']] = item['default']
        
        return (definition, error)

    def _remove_blueprint(self):
        error = None
        blueprint = None
        client = _get_client()
        try:
            blueprint = client.blueprints.delete(self.name)
        except CloudifyClientError as err:
            LOGGER.exception(err)
            error = str(err)

        return (blueprint, error)


class AppInstance(models.Model):
    name = models.CharField(max_length=50, unique=True)
    app = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
    )

    description = models.CharField(max_length=256, null=True)
    inputs = models.CharField(max_length=256, null=True)

    READY = 'ready'
    TERMINATED = 'terminated'
    FAILED = 'failed'
    CANCELLED = 'cancelled'
    PENDING = 'pending'
    STARTED = 'started'
    CANCELLING = 'cancelling'
    FORCE_CANCELLING = 'force_cancelling'
    STATUS_CHOICES = (
        (READY, 'ready'),
        (TERMINATED, 'terminated'),
        (FAILED, 'failed'),
        (CANCELLED, 'cancelled'),
        (PENDING, 'pending'),
        (STARTED, 'started'),
        (CANCELLING, 'cancelling'),
        (FORCE_CANCELLING, 'force_cancelling')
    )
    status = models.CharField(
        max_length=5,
        choices=STATUS_CHOICES,
        default=READY,
        blank=True
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    workflow_status = models.CharField(max_length=30, default="Not running")
    progress = models.CharField(max_length=30, default="-")

    queued_jobs = models.PositiveIntegerField(default=0)
    running_jobs = models.PositiveIntegerField(default=0)
    finished_jobs = models.PositiveIntegerField(default=0)

    @classmethod
    def get(cls, pk, owner, return_dict=False):
        error = None
        instance = None
        try:
            instance = cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            pass

        if instance is not None and owner != instance.owner:
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

        app, error = Application.get(app_pk)
        if error is None:
            if app is None:
                error = "Can't create instance because app doesn't exists"

        if error is None:
            try:
                instance = cls.objects.create(
                    name=deployment_id,
                    app=app,
                    description="",
                    inputs=json.dumps(
                        inputs,
                        ensure_ascii=False,
                        separators=(',', ':')),
                    status=cls.READY,
                    owner=owner)
            except Exception as err:
                LOGGER.exception(err)
                error = str(err)

        if not return_dict:
            return (instance, error)
        else:
            return {'instance': _to_dict(instance), 'error': error}

    def execute(self):
        """ Reset execution, create a new deployment and start the workflows """
        error = self.reset_execution()

        if error is None:
            # Create cfy deployment
            _, error = self.__class__._create_deployment(
                self.app.name,
                self.name,
                json.loads(self.inputs))

            if error is None:
                self.workflow_status = "Initializing"
                self.progress = "..."
                self._run_workflows()
        
        return error

    @backend
    def reset_execution(self):
        self._update_status(AppInstance.READY)

        self.workflow_status = "Not running"
        self.progress = "-"
        self.queued_jobs = 0
        self.running_jobs = 0
        self.finished_jobs = 0
        self.save()

        # logs
        logs_list, error = ApplicationInstanceLog.list(
            self,
            self.owner
        )
        if error is None:
            for log in logs_list:
                log.delete()

            # executions
            executions_list, error = WorkflowExecution.list(self)
            if error is None:
                for execution in executions_list:
                    execution.delete()
            
            time.sleep(1) # database syncronization

        return error

    @backend
    def _run_workflows(self):
        self._update_status(Execution.STARTED)

        status = self._run_workflow(WorkflowExecution.INSTALL)
        if WorkflowExecution.is_execution_finished(status) and \
                not WorkflowExecution.is_execution_wrong(status):
            status = self._run_workflow(WorkflowExecution.RUN)
            if WorkflowExecution.is_execution_finished(status) and \
                    not WorkflowExecution.is_execution_wrong(status):
                status = self._run_workflow(WorkflowExecution.UNINSTALL)

        if not WorkflowExecution.is_execution_finished(status):
            # TODO: cancel execution
            pass
        
        if WorkflowExecution.is_execution_wrong(status):
            self.workflow_status = 'Failed'
        else:
            self.workflow_status = 'Finished'
        self.progress = '-'

        self._update_status(status)

        # Finally delete cfy deployment
        self.__class__._destroy_deployment(self.name, force=True)

        # Django creates a new connection that needs to be manually closed
        connection.close()

        return status

    def _run_workflow(self, workflow):
        error = None
        execution = None

        if workflow == 'install':
            self.workflow_status = 'Bootstraping'
        elif workflow == 'uninstall':
            self.workflow_status = 'Cleaning Up'
        elif workflow == 'run_jobs':
            self.workflow_status = 'Running'
        ApplicationInstanceLog.create(
            self,
            timezone.now(),
            "-------"+self.workflow_status.upper()+"-------")
        self.progress = '...'
        self.save()

        execution, error = WorkflowExecution.create(
            self,
            workflow,
            self.owner,
            force=False)

        if error is not None:
            status = Execution.CANCELLED
            self._update_status(Execution.CANCELLED)
            message = "Couldn't execute the workflow '" + \
                workflow+"': "+error
            LOGGER.error(message)
            ApplicationInstanceLog.create(
                self,
                timezone.now(),
                message)
            return status
        if execution is None:
            status = Execution.CANCELLED
            self._update_status(Execution.CANCELLED)
            message = "Couldn't create the execution for workflow '" + \
                workflow+"'"
            LOGGER.error(message)
            ApplicationInstanceLog.create(
                self,
                timezone.now(),
                message)
            return status

        offset = 0
        finished = False
        status = Execution.PENDING
        while not finished and error is None:
            events, error = execution.get_execution_events(offset)
            if error is None:
                retries = 0
                offset = events['last']
                status = events['status']
                finished = WorkflowExecution.is_execution_finished(status)
                self.append_logs(events['logs'])
            time.sleep(5)

        return status

    def _update_status(self, status):
        if status != self.status:
            self.status = status
            self.save()

    def is_finished(self):
        return self.status in Execution.END_STATES \
            or self.status == AppInstance.READY

    def is_wrong(self):
        return self.is_finished() \
            and self.status != Execution.TERMINATED \
            and self.status != AppInstance.READY

    def append_logs(self, events_list):
        workflow_status = self.workflow_status
        progress = self.progress
        queued_jobs = self.queued_jobs
        running_jobs = self.running_jobs
        finished_jobs = self.finished_jobs
        for event in events_list:
            if not "reported_timestamp" in event:
                # this event cannot be logged
                LOGGER.warning(
                    "The event has not a timestamp, will not be registered")
                continue

            message = ""
            if "message" in event:
                message = event["message"]
            timestamp = event["reported_timestamp"]

            event_type = event["type"]
            if event_type == "cloudify_event":
                cloudify_event_type = event["event_type"]
                if cloudify_event_type == "workflow_node_event":
                    message += " " + event["node_instance_id"] + \
                        " (" + event["node_name"] + ")"
                    
                    if (len(event["message"]) > 17 \
                            and workflow_status == 'Running' \
                            and event["message"][:17] == 'State changed to '):
                        state = event["message"][17:]
                        progress = ''
                        if state == 'PENDING':
                            queued_jobs +=1
                        elif state == 'RUNNING':
                            if queued_jobs > 0:
                                queued_jobs -= 1
                            running_jobs +=1
                        elif state == 'COMPLETED':
                            if running_jobs > 0:
                                running_jobs -= 1
                            elif queued_jobs > 0:
                                queued_jobs -= 1
                            finished_jobs += 1
                        else:
                            progress = state
                        progress += str(queued_jobs)+" | "+str(running_jobs)+" | "+str(finished_jobs)
                elif cloudify_event_type == "sending_task" \
                        or cloudify_event_type == "task_started" \
                        or cloudify_event_type == "task_succeeded" \
                        or cloudify_event_type == "task_failed":
                    # message += " [" + event["operation"] + "]"
                    if "node_instance_id" in event and event["node_instance_id"]:
                        message += " " + event["node_instance_id"]
                    if "node_name" and event["node_name"]:
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

            ApplicationInstanceLog.create(self, timestamp, message)
        
        self.workflow_status = workflow_status
        self.progress = progress
        self.queued_jobs = queued_jobs
        self.running_jobs = running_jobs
        self.finished_jobs = finished_jobs
        self.save()

    @classmethod
    def get_instance_events(cls, pk, owner):
        logs_list = []
        status = None
        finished = None
        instance, error = cls.get(pk, owner)

        if error is None:
            if instance is not None:
                status = instance.status
                finished = instance.is_finished()
                logs_list, error = ApplicationInstanceLog.list(
                    instance,
                    owner
                )
            else:
                error = "Can't get instance events because it doesn't exist"

        return (
            {
                'logs': [_to_dict(log) for log in logs_list],
                'status': status,
                'finished': finished
            },
            error)


    @classmethod
    def get_status(cls, pk, owner):
        workflow_status = None
        progress = None
        running_jobs = 0
        finished_jobs = 0
        finished = True
        status = None
        instance, error = cls.get(pk, owner)

        if error is None:
            if instance is not None:
                finished = instance.is_finished()
                status = instance.status
            else:
                error = "Can't get instance events because it doesn't exist"

        return (status, finished,error)

    @classmethod
    def get_progress(cls, pk, owner):
        workflow_status = None
        progress = None
        running_jobs = 0
        finished_jobs = 0
        finished = True
        status = None
        instance, error = cls.get(pk, owner)

        if error is None:
            if instance is not None:
                workflow_status = instance.workflow_status
                progress = instance.progress
                running_jobs = instance.running_jobs
                finished_jobs = instance.finished_jobs
                finished = instance.is_finished()
                status = instance.status
            else:
                error = "Can't get instance events because it doesn't exist"

        return (
            workflow_status,
            progress,
            running_jobs,
            finished_jobs,
            finished,
            status,
            error)

    @classmethod
    def get_instance_runjobs_workflowid(cls, pk, owner, return_dict=False):
        workflowid = None
        instance, error = cls.get(pk, owner)

        if error is None:
            if instance is not None:
                # executions
                executions_list, error = WorkflowExecution.list(instance)
                if error is None:
                    for execution in executions_list:
                        if execution.workflow == WorkflowExecution.RUN:
                            workflowid = execution.id_code
                            break
                else:
                    LOGGER.warning("Couldn't get workflow list: "+error)
            else:
                error = "Can't get instance workflowid because instance doesn't exist"

        if not return_dict:
            return (workflowid, error)
        else:
            return {'workflowid': workflowid, 'error': error}

    @classmethod
    def remove(cls, pk, owner, return_dict=False, force=False):
        instance, error = cls.get(pk, owner)

        if error is None:
            if instance is not None:
                _, error = cls._destroy_deployment(
                    instance.name,
                    force=force)
                if error is None or instance.is_finished():
                    error = None
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
    def _create_deployment(cls, app_id, instance_id, inputs):
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
        except CloudifyClientError as err:
            LOGGER.exception(err)
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
            LOGGER.exception(err)
            error = str(err)

        return (deployment, error)


class ApplicationInstanceLog(models.Model):
    generated = models.DateTimeField(primary_key=True)

    instance = models.ForeignKey(
        AppInstance,
        on_delete=models.CASCADE,
    )

    message = models.TextField()

    @classmethod
    def list(cls, instance, owner, return_dict=False):
        error = None
        logs_list = []
        try:
            logs_list = \
                cls.objects.filter(instance=instance).order_by('-generated')
        except cls.DoesNotExist:
            pass

        if not return_dict:
            return (logs_list, error)
        else:
            return {
                'logs_list': [_to_dict(log) for log in logs_list],
                'error': error}

    @classmethod
    def create(cls, instance, generated, message):
        error = None

        if instance is None:
            error = 'Application instance does not belong to user'
        else:
            try:
                instance = cls.objects.create(
                    instance=instance,
                    generated=generated,
                    message=message)
            except IntegrityError as err:
                LOGGER.warning(err)
                error = str(err)
            except Exception as err:
                LOGGER.exception(err)
                error = str(err)

        return error


class WorkflowExecution(models.Model):
    INSTALL = 'install'
    RUN = 'run_jobs'
    UNINSTALL = 'uninstall'

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

        if execution is not None and owner != execution.owner:
            execution = None
            error = 'Instance execution does not belong to user'

        if not return_dict:
            return (execution, error)
        else:
            if execution is not None:
                execution = _to_dict(execution)
            return {'execution': execution, 'error': error}

    @classmethod
    def list(cls, instance, return_dict=False):
        error = None
        execution_list = []
        try:
            execution_list = cls.objects.filter(
                app_instance=instance)
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
    def create(cls, instance, workflow, owner,
               force=False, params=None, return_dict=False):
        error = None
        execution = None

        if instance is None:
            error = "Can't create execution because instance doesn't exist"
        elif instance.owner != owner:
            error = \
                "Can't create execution because instance doesn't " +\
                "belong to user"
        else:
            execution, error = cls._execute_workflow(
                instance.name,
                workflow,
                force,
                params)

        if error is None:
            try:
                execution = cls.objects.create(
                    id_code=execution['id'],
                    app_instance=instance,
                    workflow=workflow,
                    created_on=timezone.now(),
                    owner=owner)
            except Exception as err:
                print("error! "+err)
                LOGGER.exception(err)
                error = str(err)
                # TODO: cancel execution

        if not return_dict:
            return (execution, error)
        else:
            return {'execution': _to_dict(execution), 'error': error}

    def __str__(self):
        return "Workflow execution {0}:{1} [{2}] from {3}".format(
            self.workflow,
            self.app_instance.name,
            self.id_code,
            self.owner.username)

    @staticmethod
    def _execute_workflow(deployment_id, workflow, force, params=None):
        error = None
        execution = None

        client = _get_client()
        while True:
            try:
                execution = client.executions.start(deployment_id,
                                                    workflow,
                                                    parameters=params,
                                                    force=force)
                break
            except (
                DeploymentEnvironmentCreationPendingError,
                DeploymentEnvironmentCreationInProgressError) as err:
                LOGGER.warning(err)
                time.sleep(WAIT_FOR_EXECUTION_SLEEP_INTERVAL)
                continue
            except CloudifyClientError as err:
                error = str(err)
                LOGGER.exception(err)
            break

        return (execution, error)

    def get_execution_events(self, offset, return_dict=False):
        events = self._get_execution_events(offset)

        if not return_dict:
            return (events, None)
        else:
            return {'events': events, 'error': None}

    def _get_execution_events(self, offset):
        client = _get_client()

        # TODO: manage errors
        cfy_execution = client.executions.get(self.id_code)
        events = client.events.list(execution_id=self.id_code,
                                    _offset=offset,
                                    _size=100,
                                    include_logs=True)
        last_message = events.metadata.pagination.total

        return {
            'logs': events.items,
            'last': last_message,
            'status': cfy_execution.status
        }

    @classmethod
    def is_execution_finished(cls, status):
        return status in Execution.END_STATES

    @classmethod
    def is_execution_wrong(cls, status):
        return cls.is_execution_finished(status) and status != Execution.TERMINATED
