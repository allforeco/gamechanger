from django.template import loader
from django.http import HttpResponse
from django.shortcuts import redirect
from django import forms

from .models import Location, Country, Organization, OrganizationContact

import datetime
import csv
import pycountry

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
            category=Country.pycy_lookup(row[4][:200])
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
      cy = Country.pycy_lookup(contact.category)
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

