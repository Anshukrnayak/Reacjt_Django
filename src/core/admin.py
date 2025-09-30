from django.contrib import admin
from .models import ClientModel,DesignationModel,LeadModel

admin.site.register(DesignationModel)
admin.site.register(ClientModel)
admin.site.register(LeadModel)
