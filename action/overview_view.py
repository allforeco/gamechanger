from django.template import loader
from django.http import HttpResponse
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
#from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from django import forms
from .models import Gathering, Gathering_Belong, Gathering_Witness, Location, UserHome, Organization
import datetime

static_location_file = "/var/www/gamechanger.eco/static/cached_locations.htmlbody"

def latest_records_view(request):
  filter_amount = int(request.POST.get('filter_amount', '200'))
  record_list = list(Gathering_Witness.objects.order_by("-updated")[:filter_amount])
  witness_dict = {}
  print(f"LRV1 {len(record_list)}")
  for record in record_list:
    #print(f"LRV2 {record}")
    try:
      belong_regid = record.set_gathering_to_root()
      witness_dict[(belong_regid,record.date)] = record
    except:
      print(f"LRV4 Broken witness {record}")

  witness_list = list(witness_dict.values())
  witness_list.sort(key=lambda e: e.updated, reverse=True)
  print(f"LRV3 {len(witness_list)}")
  template = loader.get_template('action/latest_records_view.html')
  context = {
    'filter_amount': filter_amount,
    'record_list': witness_list,
  }

  return HttpResponse(template.render(context, request))

def locations_view(request):
  #print(f"LEND {len(list(Location.objects.all()))} | {len(Location.valid_ids())}")

  logginbypass = False
  location_list=list()
  #FIXME: Remove static template file
  #template = loader.get_template('static/locations_overview.html')
  template = loader.get_template('action/spooled_locations_overview.html')
  htmlbody = ""

  if request.user.is_authenticated or logginbypass:
    template = loader.get_template('action/locations_overview.html')
    location_list = Location.countries(False)
    location_list.sort(key=lambda e: e[0], reverse=False)
    for location in location_list:
      location[2].sort(key=lambda e: e[0], reverse=False)
  else:
    try:
      with open(static_location_file, "r") as text:
        htmlbody = text.read()
    except:
      htmlbody = """<tr><td colspan="2"><h1>Data currently not available.</h1></td></tr>"""

  context = {
    'location_list': location_list,
    'logginbypass': logginbypass,
    'htmlbody': htmlbody,
  }

  return HttpResponse(template.render(context, request))

def organizations_view(request):
  organizations_list = Organization.objects.all().order_by('primary_location')

  organizations_region_dict = {}
  for organization in organizations_list:
    if not organization.primary_location in organizations_region_dict.keys():
      organizations_region_dict[organization.primary_location] = [organization]
    else:
      organizations_region_dict[organization.primary_location] += [organization]

  print("o_r_d", organizations_region_dict)
  template = loader.get_template('action/organizations_overview.html')
  context = {'organizations_region_dict':organizations_region_dict}

  return HttpResponse(template.render(context, request))

def organization_view(request, organizationname):
  organization = Organization.objects.filter(name=organizationname).first()
  template = loader.get_template('action/organization_overview.html')
  context = {'organization':organization}

  return HttpResponse(template.render(context, request))

def help_view(request):

  print(f"PLVI |{Location.valid_ids(False)}|")

  template = loader.get_template('action/help_overview.html')
  context = {

  }

  return HttpResponse(template.render(context, request))