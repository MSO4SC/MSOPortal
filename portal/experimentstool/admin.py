from django.contrib import admin
from .models.data import DataCatalogueKey
from .models.connection import TunnelConnection
from .models.hpc import HPCInstance
from .models.application import (
    Application,
    AppInstance,
    WorkflowExecution
)

admin.site.register(Application)
admin.site.register(AppInstance)
admin.site.register(WorkflowExecution)
admin.site.register(HPCInstance)
admin.site.register(TunnelConnection)
admin.site.register(DataCatalogueKey)
