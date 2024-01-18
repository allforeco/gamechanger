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
import pycountry

'''
???chached locations
'''
static_location_file = "/var/www/gamechanger.eco/static/cached_locations.htmlbody"

'''
___pycountry lookup
'''
def pycy_lookup(name):
  try:
    if pycountry.countries.get(alpha_2=name):
      pycy = pycountry.countries.get(alpha_2=name)
    elif pycountry.countries.get(alpha_3=name):
      pycy = pycountry.countries.get(alpha_3=name)
    elif pycountry.countries.get(name=name):
      pycy = pycountry.countries.get(name=name)
    elif pycountry.countries.get(official_name=name):
      pycy = pycountry.countries.get(official_name=name)
    elif pycountry.countries.search_fuzzy(name):
      pycy = pycountry.countries.search_fuzzy(name)[0]
    
    if Country.objects.filter(name=pycy.name).exists():
      return Country.objects.get(name=pycy.name)
    else:
      return Country.Unknown()
  except:
    return Country.Unknown()

'''
???startpage latest 200 updated gathering_witness
'''
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

'''
???locations list view
___static/generated by loginstatus
'''
def locations_view(request):
  #print(f"LEND {len(list(Location.objects.all()))} | {len(Location.valid_ids())}")
  #Country.generate()
  logginbypass = True
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

'''
___import contact information by reading csv
___option to purge exsistic contacts before import
'''
def contacts_import(request, option=0):
  
  logginbypass = False
  if request.user.is_authenticated or logginbypass:
    print("CIS", "contat import start")
    fieldnames = ['contacttype','address','info','location','category','organization','source']
    csvfilepath = request.GET['filepath']

    #print(csvfilepath)
    if not csvfilepath:
      #http://127.0.0.1:8000/action/contacts/import/1?purgesrc=https://docs.google.com/spreadsheets/d/17ADogMNYXGzBBCtLFe7XCl8EBDrZCVExr6KMSV3HwxI&filepath=/home/vbx/Documents/VSc/FFF/gamechanger/dev_tools/CSA.csv
      return redirect('action:contacts_list')
    
    datalenght = 201
    datalenghtcounter = 0

    if option==1:
      purgesrc = request.GET['purgesrc']
      OrganizationContact.objects.filter(source=purgesrc).delete()

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
          
          if not location:
            location = Location.Unknown()

          if location.id == -1:
            category=pycy_lookup(row[4][:200])
            location = category.country_location()
            oc.location=location
          else:
            category=location.in_country #row[4][:200]
          
          if category == Country.Unknown():
            continue

          oc.category=category.name
          
          oc.organizationTitle=row[5][:200]
          organization=Organization.objects.filter(name__iexact=row[5][:200]).first() or Organization.objects.get(id=-1)
          oc.organization=organization #row[5][:200]
          
          oc.source=row[6][:200]

          oc.save()
          #print(oc)

        skiptitle=False
        datalenghtcounter+=1
        if datalenghtcounter > datalenght:
          0
          #break
  
  print("CIC", "contat import complete")
  return redirect('action:contacts_list')

'''
___view for contacts by country->region
'''
def contacts_view(request):
  def sortalg(contact):
    ct=contact.contacttype
    v=0
    if ct==OrganizationContact.EMAIL:
      return v
    v+=1
    if ct==OrganizationContact.PHONE:
      return v
    v+=1
    if ct==OrganizationContact.WEBSITE:
      return v
    v+=1
    if ct==OrganizationContact.FACEBOOK:
      return v
    v+=1
    if ct==OrganizationContact.INSTAGRAM:
      return v
    v+=1
    if ct==OrganizationContact.TWITTER:
      return v
    v+=1
    if ct==OrganizationContact.YOUTUBE:
      return v
    v+=1
    if ct==OrganizationContact.LINKEDIN:
      return v
    return v+ord(ct[0])
  
  def sortalgR(contact):
    return -sortalg(contact)

  contacts_list = OrganizationContact.objects.all().order_by('locationTitle')
  UNKNOWN = (Country.Unknown().name, Country.Unknown().id)

  contacts_region_dict = {}
  for contact in contacts_list:
    location=tuple()
    category=tuple()

    if contact.location != Location.Unknown:
      location = (contact.location.name, contact.location.id)
    else:
      location= (contact.locationTitle, Location.Unknown.id)

    if contact.category and contact.category != Country.Unknown().name:
      cy = pycy_lookup(contact.category)
      category = (cy.name, cy.country_location().id)

      if location[1] == -1:
        location = category
    else:
      category=UNKNOWN
      continue
    
    
    if not category in contacts_region_dict.keys():
      contacts_region_dict[category] = {}
      contacts_region_dict[category][category] = []
      contacts_region_dict[category][location] = [contact]
    else:
      if not location in contacts_region_dict[category].keys():
        contacts_region_dict[category][location] = [contact]
      else:
        contacts_region_dict[category][location] += [contact]
    
    contacts_region_dict[category][location].sort(reverse=False, key=sortalg)
  
  contacts_region_dict = dict(sorted(contacts_region_dict.items()))
  template = loader.get_template('action/contacts_overview.html')
  context = {
    'contacts_region_dict': contacts_region_dict,
    'autocollapse': True  
  }

  return HttpResponse(template.render(context, request))

'''
___formclass for contact
'''
class OrganizationcontactCreateForm(forms.ModelForm):
  class Meta():
    model = OrganizationContact
    fields = ['contacttype', 'address', 'info', 'organization', 'location']

'''
___form view for contact
'''
def OrganizationcontactCreateSubmit(request):
  logginbypass = False
  if not (request.user.is_authenticated or logginbypass): return redirect('action:start')
  template = loader.get_template('action/form_CreateSubmit.html')
  context = {'form': OrganizationcontactCreateForm(), 'createsubmit_title': "Organization Contact", 'formaction_url': "create_organizationcontact"}
  return HttpResponse(template.render(context, request))

'''
___create contact by form data
___redirect loop
'''
def OrganizationcontactCreate(request):
  data = request.POST
  print(data)

  try:
    contacttype= data['contacttype']
    address=data['address']
    info=data['info']
    organization=Organization.objects.get(id=data['organization'])
    location=Location.objects.get(id=data['location'])
  except:
    return redirect('action:organizationcontact_submit')
  
  organizationcontact = OrganizationContact()
  organizationcontact.contacttype = contacttype
  organizationcontact.address = address
  organizationcontact.info = info
  organizationcontact.organization=organization
  organizationcontact.location=location
  organizationcontact.save()

  return redirect('action:organizationcontact_submit')

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

'''
___organization formclass
'''
class OrganizationCreateForm(forms.ModelForm):
  class Meta():
    model = Organization
    fields = ['name']

'''
___organization form view
'''
def OrganizationCreateSubmit(request):
  logginbypass = False
  if not (request.user.is_authenticated or logginbypass): return redirect('action:start')
  template = loader.get_template('action/form_CreateSubmit.html')
  context = {'form': OrganizationCreateForm(), 'createsubmit_title': "Organization", 'formaction_url': "create_organization"}
  return HttpResponse(template.render(context, request))

'''
___Organization create by form
___contact redirect
'''
def OrganizationCreate(request):
  data = request.POST
  print(data)

  try:
    name = data['name']
  except:
    redirect('action:organization_submit')

  organization = Organization()
  organization.name = name
  organization.verified = False
  organization.save()
  return redirect('action:organizationcontact_submit')

'''UNUSED
___view for user guide
'''
def help_view(request):

  print(f"PLVI |{Location.valid_ids(False)}|")

  template = loader.get_template('action/help_overview.html')
  context = {

  }

  return HttpResponse(template.render(context, request))