from django.contrib import admin
from django.http import *

# Register your models here.

from .models import Country, Location, Organization, OrganizationContact, UserHome, Action, Gathering, Gathering_Witness

admin.site.register(UserHome)
admin.site.register(Action)

class GatheringAdmin(admin.ModelAdmin):
  list_display = ('regid', 'location', 'start_date')
  ordering = ('location', 'regid')
  search_fields = ['regid', 'location', 'start_date']


admin.site.register(Gathering, GatheringAdmin)

class GatheringWitnessAdmin(admin.ModelAdmin):
  list_display = ('gathering', 'date', 'participants', 'organization')
  ordering = ('-date',)
  search_fields = ['date', 'organization']


admin.site.register(Gathering_Witness, GatheringWitnessAdmin)

class LocationAdmin(admin.ModelAdmin):
  list_display = ('name', 'str_lat_lon', 'in_country', 'verified')
  ordering = ('name',)
  search_fields = ['name']

class CountryAdmin(admin.ModelAdmin):
  list_display = ('name', 'code', 'flag')
  ordering = ('name',)
  search_fields = ['name']

admin.site.register(Country, CountryAdmin)
admin.site.register(Location, LocationAdmin)

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
  list_display = ('address', 'contacttype', 'category', 'location', 'organization')
  search_fields =['address']

  def get_form(self, request, obj=None, **kwargs):
    form = super(OrganizationContactAdmin, self).get_form(request, obj, **kwargs)
    form.base_fields['organization'].queryset = Organization.objects.exclude(verified=0).order_by('name')
    form.base_fields['location'].queryset = Location.objects.all().order_by('name')
    return form

admin.site.register(OrganizationContact, OrganizationContactAdmin)

