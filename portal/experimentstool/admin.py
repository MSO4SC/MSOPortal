from django.contrib import admin
from .models import (
    Application,
    AppInstance,
    WorkflowExecution,
    TunnelConnection,
    HPCInfrastructure,
    DataCatalogueKey
)

admin.site.register(Application)
admin.site.register(AppInstance)
admin.site.register(WorkflowExecution)
admin.site.register(HPCInfrastructure)
admin.site.register(TunnelConnection)
admin.site.register(DataCatalogueKey)
