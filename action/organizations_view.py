from django.template import loader
from django.http import HttpResponse
from django.shortcuts import redirect
from django import forms

from .models import Organization, OrganizationContact, Gathering_Witness

'''
___organization list view
'''
def organizations_view(request):
  organizations_list = Organization.objects.exclude(primary_location=None).order_by('primary_location')

  organizations_region_dict = {}
  for organization in organizations_list:
    contacts = OrganizationContact.objects.filter(organization=organization)
    if not organization.primary_location.country() in organizations_region_dict.keys():
      organizations_region_dict[organization.primary_location.country()] = [[organization,contacts]]
    else:
      organizations_region_dict[organization.primary_location.country()] += [[organization,contacts]]

  template = loader.get_template('action/organizations_overview.html')
  context = {'organizations_region_dict':organizations_region_dict}

  return HttpResponse(template.render(context, request))

'''
___organization view by id
'''
def organization_view(request, orgid):
  template = loader.get_template('action/organization_overview.html')

  organization = Organization.objects.filter(id=orgid).first()
  #organization = Organization.objects.first()
  if organization == None:
    context={
      'organization':None,
      'contact_list': [],
      'gathering_witness_list': [],
    }
    return HttpResponse(template.render(context, request))
  contact_list = OrganizationContact.objects.filter(organization=organization)
  gathering_witness_list = Gathering_Witness.objects.filter(organization=organization).order_by('-date')[:100]
  #print("org", organization)
  #print("cl", contact_list)
  #print("gwl", gathering_witness_list)
  
  context = {
    'organization':organization,
    'contact_list': contact_list,
    'gathering_witness_list': gathering_witness_list,
    }

  return HttpResponse(template.render(context, request))

