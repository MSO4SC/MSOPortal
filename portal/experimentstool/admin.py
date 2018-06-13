from django.contrib import admin
from .models import (
    Application,
    AppInstance,
    WorkflowExecution,
    HPCInfrastructure,
    DataCatalogueKey
)

admin.site.register(Application)
admin.site.register(AppInstance)
admin.site.register(WorkflowExecution)
admin.site.register(HPCInfrastructure)
admin.site.register(DataCatalogueKey)
