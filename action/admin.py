from django.contrib import admin
from django.http import *

# Register your models here.

from .models import Country, Location, Location_Belong, Organization, OrganizationContact, UserHome, Action, Gathering, Gathering_Witness, Verification, Steward

admin.site.register(UserHome)
admin.site.register(Action)
admin.site.register(Verification)

admin.site.register(Steward)

class GatheringAdmin(admin.ModelAdmin):
  list_display = ('regid', 'location', 'start_date', 'steward')
  ordering = ('location', 'regid')
  search_fields = ['regid', 'location', 'start_date']
  autocomplete_fields = ['location']


admin.site.register(Gathering, GatheringAdmin)

class GatheringWitnessAdmin(admin.ModelAdmin):
  list_display = ('gathering', 'date', 'participants', 'organization')
  ordering = ('-date',)
  search_fields = ['date', 'organization']


admin.site.register(Gathering_Witness, GatheringWitnessAdmin)

class LocationAdmin(admin.ModelAdmin):
  list_display = ('name', 'str_lat_lon', 'in_country', 'creation_details',)
  ordering = ('name',)
  search_fields = ['name']
  autocomplete_fields = ['in_country', 'in_location']

class CountryAdmin(admin.ModelAdmin):
  list_display = ('name', 'code', 'flag')
  ordering = ('name',)
  search_fields = ['name']

class Location_BelongAdmin(admin.ModelAdmin):
  #autocomplete_fields = ['prime', 'duplicate']
  raw_id_fields = ['prime', 'duplicate']
  @admin.display()
  def dis(self):
    return "return"
  

admin.site.register(Country, CountryAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Location_Belong, Location_BelongAdmin)

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
  autocomplete_fields = ['location', 'organization']

  def get_form(self, request, obj=None, **kwargs):
    form = super(OrganizationContactAdmin, self).get_form(request, obj, **kwargs)
    form.base_fields['organization'].queryset = Organization.objects.exclude(verified=0).order_by('name')
    form.base_fields['location'].queryset = Location.objects.all().order_by('name')
    return form

admin.site.register(OrganizationContact, OrganizationContactAdmin)

