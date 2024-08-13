from django.template import loader
from django.http import HttpResponse
from django.shortcuts import redirect
from django import forms

from .models import Organization, OrganizationContact, Gathering_Witness, Gathering

'''
___organization list view
'''
def organizations_view(request):
  organizations_list = Organization.objects.exclude(primary_location=None).order_by('primary_location')

  organizations_region_dict = {}
  for organization in organizations_list:
    contacts = OrganizationContact.objects.filter(organization=organization)
    if not organization.primary_location.country_location() in organizations_region_dict.keys():
      organizations_region_dict[organization.primary_location.country_location()] = [[organization,contacts]]
    else:
      organizations_region_dict[organization.primary_location.country_location()] += [[organization,contacts]]

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
  gathering_list = Gathering.objects.filter(organizations__in=[organization])
  gathering_witness_list = Gathering_Witness.objects.filter(organization=organization).order_by('-date')[:100]

  event_head = Gathering.datalist_template(date=True, location=True, gtype=False, activity_type=True, participants=True, recorded_link=True, map_link=True, overview=True, recorded=True, record=True, model=True)
  event_list = []

  for gw in gathering_witness_list:
    event_list.append(Gathering.datalist(gw, True, event_head))

  for g in gathering_list:
    event_list.append(Gathering.datalist(g, False, event_head))
  
  event_list.sort(key=lambda e: e['date'], reverse=True)

  context = {
    'organization':organization,
    'contact_list': contact_list,
    'gathering_witness_list': gathering_witness_list,
    'event_head':event_head,
    'event_list':event_list,
    'logginbypass': True,
    }

  return HttpResponse(template.render(context, request))

