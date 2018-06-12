from django.contrib import admin
from .models import Application, AppInstance, WorkflowExecution, HPCInfrastructure

admin.site.register(Application)
admin.site.register(AppInstance)
admin.site.register(WorkflowExecution)
admin.site.register(HPCInfrastructure)
