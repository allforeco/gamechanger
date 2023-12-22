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

class OrganizationAdmin(admin.ModelAdmin):
  list_display = ('name', 'verified')
  search_fields = ['name']
  ordering = ('-verified','name',)

  #def get_form(self, request, obj=None, **kwargs):
  #  form = super(OrganizationAdmin, self).get_form(request, obj, **kwargs)
  #  form.base_fields['primary_location'].queryset = Location.objects.all().order_by('name')
  #  return form

admin.site.register(Organization,OrganizationAdmin)

class OrganizationContactAdmin(admin.ModelAdmin):
  list_display = ('address', 'contacttype', 'location', 'organization')
  search_fields =['address']

  def get_form(self, request, obj=None, **kwargs):
    form = super(OrganizationContactAdmin, self).get_form(request, obj, **kwargs)
    form.base_fields['organization'].queryset = Organization.objects.exclude(verified=0).order_by('name')
    form.base_fields['location'].queryset = Location.objects.all().order_by('name')
    return form

admin.site.register(OrganizationContact, OrganizationContactAdmin)

