from django.contrib import admin
from .models import Application, AppInstance, Execution, HPCInfrastructure

admin.site.register(Application)
admin.site.register(AppInstance)
admin.site.register(Execution)
admin.site.register(HPCInfrastructure)
