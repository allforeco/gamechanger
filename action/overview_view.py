from django.template import loader
from django.http import HttpResponse
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
#from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import redirect
from django import forms
from .models import Gathering, Gathering_Belong, Gathering_Witness, Location, Country, UserHome, Organization, OrganizationContact
import datetime
import csv

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
  #Country.generate()
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


def contacts_import(request, option=0):
  logginbypass = False
  if request.user.is_authenticated or logginbypass:
    fieldnames = ['contacttype','address','info','location','category','organization','source']
    csvfilepath = 'dev_tools/CSA.csv'
    
    datalenght = 201
    datalenghtcounter = 0

    if option==1:
      OrganizationContact.objects.all().delete()

    with open(csvfilepath) as csvfile:
      reader = csv.reader(csvfile)

      skiptitle = True
      for row in reader:
        #print(row)
        if not skiptitle:
          oc = OrganizationContact()
          oc.contacttype=row[0][:4]
          oc.address=row[1][:200] 
          oc.info=row[2][:200]
          
          oc.locationTitle=row[3][:200]
          location=Location.objects.filter(name__iexact=row[3][:200]).first() or Location.objects.get(id=-1)
          oc.location=location #row[3][:200]
          
          if location.id == -1:
            category=row[4][:200]
          else:
            category=location.country() #row[4][:200]
          
          oc.category=category
          
          oc.organizationTitle=row[5][:200]
          organization=Organization.objects.filter(name__iexact=row[5][:200]).first() or Organization.objects.get(id=-1)
          oc.organization=organization #row[5][:200]
          
          oc.source=row[6][:200]
          oc.save()
          print(oc)

        skiptitle=False
        datalenghtcounter+=1
        if datalenghtcounter > datalenght:
          0
          #break

  return redirect('action:contacts_list')

def contacts_view(request):
  contacts_list = OrganizationContact.objects.all().order_by('-locationTitle')

  contacts_region_dict = {}
  for contact in contacts_list:
    

    if contact.location:
      location = (contact.locationTitle, contact.location.id)
    else:
      location=tuple(['Region',-1])

    if contact.category:
      category = (contact.category, contact.location.country().id)
    else:
      category=tuple(['Global',-1])
    
    if not category in contacts_region_dict.keys():
      contacts_region_dict[category] = {}
      contacts_region_dict[category][location] = [contact]
    else:
      if not location in contacts_region_dict[category].keys():
        contacts_region_dict[category][location] = [contact]
      else:
        contacts_region_dict[category][location] += [contact]
  
  contacts_region_dict = dict(sorted(contacts_region_dict.items()))
  template = loader.get_template('action/contacts_overview.html')
  context = {'contacts_region_dict': contacts_region_dict}

  return HttpResponse(template.render(context, request))


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
  print("org", organization)
  print("cl", contact_list)
  print("gwl", gathering_witness_list)
  
  context = {
    'organization':organization,
    'contact_list': contact_list,
    'gathering_witness_list': gathering_witness_list,
    }

  return HttpResponse(template.render(context, request))

def help_view(request):

  print(f"PLVI |{Location.valid_ids(False)}|")

  template = loader.get_template('action/help_overview.html')
  context = {

  }

  return HttpResponse(template.render(context, request))