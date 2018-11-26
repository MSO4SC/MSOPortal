from django.contrib import admin
from .models.data import DataCatalogueKey
from .models.infrastructure import (
    ComputingInfrastructure,
    ComputingInstance
)
from .models.application import (
    Application,
    AppInstance,
    ApplicationInstanceLog,
    WorkflowExecution
)

admin.site.register(Application)
admin.site.register(AppInstance)
admin.site.register(ApplicationInstanceLog)
admin.site.register(WorkflowExecution)
admin.site.register(ComputingInfrastructure)
admin.site.register(ComputingInstance)
admin.site.register(DataCatalogueKey)
