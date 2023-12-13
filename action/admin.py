from django.contrib import admin
from django.http import *

# Register your models here.

from .models import Country, Location, Organization, OrganizationContact, UserHome, Action, Gathering, Gathering_Witness

admin.site.register(Country)
admin.site.register(Location)

admin.site.register(UserHome)
admin.site.register(Action)
admin.site.register(Gathering)
admin.site.register(Gathering_Witness)

class OrganizationContactAdmin(admin.ModelAdmin):
  def get_form(self, request, obj=None, **kwargs):
    form = super(OrganizationContactAdmin, self).get_form(request, obj, **kwargs)
    form.base_fields['organization'].queryset = Organization.objects.exclude(primary_location=None).order_by('name')
    return form

class OrganizationAdmin(admin.ModelAdmin):
  list_display = ('name', 'primary_location')
  search_fields = ['name']

  def get_form(self, request, obj=None, **kwargs):
    form = super(OrganizationAdmin, self).get_form(request, obj, **kwargs)
    form.base_fields['primary_location'].queryset = Location.objects.all().order_by('name')
    return form


admin.site.register(Organization, OrganizationAdmin)
admin.site.register(OrganizationContact, OrganizationContactAdmin)
