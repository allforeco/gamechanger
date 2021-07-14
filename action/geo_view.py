#   Gamechanger Action Views
#   Copyright (C) 2020 Jan Lindblad
# 
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
# 
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

from django.template import loader
from django.http import HttpResponse
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from django import forms
from .models import Gathering, Gathering_Belong, Gathering_Witness, Location, UserHome, Organization
from django.shortcuts import redirect
import datetime

def geo_view_handler(request, locid):
  #print(f"TOWH {locid}")
  this_location = Location.objects.filter(id=locid).first()
  if not (this_location):
    return redirect('action:geo_invalid')

  parent_location = this_location.in_location
  sublocation_list = Location.objects.filter(in_location=this_location).order_by('name')
  gathering_list = Gathering.objects.filter(location=this_location)
  witness_dict = {}
  #print(f"TOWH {this_location} {parent_location} {len(sublocation_list)} {len(gathering_list)}")
  for gathering in gathering_list:
    raw_witness_list = list(Gathering_Witness.objects.filter(gathering=gathering))
    #print(f"TOWI {gathering} {len(raw_witness_list)} {raw_witness_list}")
    for w in raw_witness_list:
      witness_dict[(w.gathering.regid,w.date)] = w
  witness_list = list(witness_dict.values())
  witness_list.sort(key=lambda e: e.date, reverse=True)
  total_participants = sum([w.participants for w in witness_list if w.participants])
  template = loader.get_template('action/geo_view.html')
  try:
    favorite_location = UserHome.objects.get(callsign=request.user.username).favorite_locations.filter(name=this_location.name).exists()
  except:
    favorite_location = False
  
  new_report = Gathering_Witness()
  context = {
    'this_location': this_location,
    'parent_location': parent_location,
    'sublocation_list': sublocation_list,
    'witness_list': witness_list,
    'total_participants': total_participants,
    'favorite_location': favorite_location,
  }

  if request.POST.get('favorite'):
    #print(f"FAVV {request.POST.get('favorite')}")
    handle_favorite(request, this_location.id)

  if request.user.is_authenticated:
    #print(f"FAVU User {request.user.username}")
    try:
      userhome = UserHome.objects.get(callsign=request.user.username)
      gathering = Gathering.objects.filter(location=locid).first()
      context['favorite_location'] = str(gathering.location.id in [loc.id for loc in userhome.favorite_locations.all()])
      #print(f"FAVQ {context['favorite_location']} {gathering.location.id} {userhome.favorite_locations.all()}")
    except:
      #print(f"FAVF No userhome object for user {request.user.username}")
      userhome = None

  return HttpResponse(template.render(context, request))

def geo_date_view_handler(request, locid, date):
  print(f"TODH {locid} {date}")
  this_location = Location.objects.filter(id=locid).first()
  parent_location = this_location.in_location
  template = loader.get_template('action/geo_date_view.html')
  context = {
    'date': date,
    'this_location': this_location,
    'parent_location': parent_location,
  }
  return HttpResponse(template.render(context, request))

def geo_update_view(request):
  witness_id = request.POST.get('witness_id')

  if (witness_id != 'None'):
    witness = Gathering_Witness.objects.get(id=witness_id)
    date = witness.date
    participants = witness.participants
    proof_url = witness.proof_url
    organization = witness.organization
  else:
    date = datetime.datetime.today()
    participants = 1
    proof_url = ""
    organization = ""
  
  locid = request.POST.get('locid')
  this_location = Location.objects.filter(id=locid).first()
  isnewevent = request.POST.get('isnewevent')

  template = loader.get_template('action/geo_update_view.html')
  context = { 
    'date': date,
    'participants': participants,
    'proof_url': proof_url,
    'organization': organization,
    'witness_id': witness_id,
    'this_location': this_location,
    'isnewevent': isnewevent,
    'gathering_types': Gathering.gathering_type.field.choices,
  }

  return HttpResponse(template.render(context, request))

def geo_add_view(request):
  witness_id = request.POST.get('witness_id')
  print("geo_add_view: witness_id =", witness_id)
  if (witness_id != 'None'):
    witness = Gathering_Witness.objects.get(id=witness_id)
    date = witness.date
    participants = witness.participants
    proof_url = witness.proof_url
    organization = witness.organization
  else:
    date = datetime.datetime.today()
    participants = 1
    proof_url = ""
    organization = ""
  
  locid = request.POST.get('locid')
  this_location = Location.objects.filter(id=locid).first()
  isnewevent = True
  print("geo_add_view: isnewevent: ", isnewevent)
  template = loader.get_template('action/geo_add_view.html')
  context = { 
    'date': date,
    'participants': participants,
    'proof_url': proof_url,
    'organization': organization,
    'witness_id': witness_id,
    'this_location': this_location,
    'isnewevent': isnewevent,
    'gathering_types': Gathering.gathering_type.field.choices,
  }

  return HttpResponse(template.render(context, request))

def geo_add_post(request):
  isnewevent = request.POST.get('isnewevent')
  print("geo_add_post: isnewevent: ", isnewevent)
  return geo_update_post_gathering(request)

def geo_update_post(request):
  isnewevent = request.POST.get('isnewevent')
  if (isnewevent == 'True'):
    return geo_update_post_gathering(request)
  else:
    return geo_update_post_witness(request)

def geo_update_post_witness(request):
  locid = request.POST.get('locid')
  witness_id = request.POST.get('witness_id')
    
  gatheringwitness = None
  witness = None
  if witness_id != "None" and witness_id != None:
    print("geo_update_post_witness: ", witness_id)
    witness = Gathering_Witness.objects.get(id=witness_id)
  else: 
    # Try to find a witness from other gatherings at this location
    try:
      # Is DEMO default for Add Date? Assuming it is, add gathering_type to filter
      # The gatherings should also be sorted to avoid random behaviour, 
      # e.g. sorr on start date descending i.e. use the 
      # latest event as default for missing information
      gatheringobjs = Gathering.objects.filter(location__id=locid, gathering_type="DEMO").order_by("-start_date")
      for go in gatheringobjs:
        if go.regid != "":
          gatheringbelong = Gathering_Belong.objects.filter(regid=go.regid).first()
          gatheringwitness = Gathering_Witness.objects.filter(gathering_id=gatheringbelong.gathering_id).first()
          witness = Gathering_Witness.objects.filter(gathering_id=gatheringwitness.id).first()
          print(go.regid, go.start_date)
          break # to use the first found
    except:
      print("geo_view.py: failed to get a witness object")


# if the above failed and witness is still None
  if witness == None:
     witness = Gathering_Witness(gathering=Gathering.objects.filter(location__id=locid).first())

  #RuntimeWarning: DateTimeField Gathering_Witness.updated received a naive datetime (2021-05-07 11:52:41.502616) while time zone support is active.
  witness.date = datetime.datetime.strptime(request.POST.get('date'), '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)
  witness.participants = request.POST.get('participants')
  witness.proof_url = request.POST.get('proof_url','')
  try:
    org = Organization.objects.get(id=request.POST.get('organization'))
    if org.name == 'None':
      org = None
      print("No organization has been selected? setting org to None.")
  except:
    org = None
  witness.organization = org 
  
  if gatheringwitness:
    witness.gathering = gatheringwitness.gathering
    if org == None:
      # one could use the latest organization as default if none was selected
      witness.org = org 

  witness.updated = datetime.datetime.today()
  witness.save()

  print(f"GUPW {witness.__dict__}")
  return redirect('action:geo_view', locid)

def geo_update_post_gathering(request):
  gathering = Gathering()
  locid = request.POST.get('locid')
  gathering.location_id = locid
  gathering.start_date = datetime.datetime.strptime(request.POST.get('date'), '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)
  gathering.end_date = datetime.datetime.strptime(request.POST.get('date'), '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc) + datetime.timedelta(weeks=int(request.POST.get('weeks')))
  gathering.expected_participants = request.POST.get('participants')
  gathering.gathering_type = request.POST.get('gathering-type')
  try:
    organization = Organization.objects.get(id=request.POST.get('organization'))
    gathering.organizations.add(organization)
  except:
    print(f"GUPO <Organization:None>")

# Regid presumably set automatically in the gamechanger database.
# It is not set automatically here when running in an offline version of gamechanger
# When running offline regid therefore ends up as an empty string in the database 
# => empty map pin, i.e. https://map.fridaysforfuture.org/?e=

# There are no gatherings with empty regid in the database dump, so probably this only happens offline?
# Creating a dummy regid just to be able to continue:
  create_dummy_regid = True
  if create_dummy_regid:
    import random
    import string
    new_regid = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    gathering.regid = new_regid
    print("new gathering regid created=", new_regid)  

  gathering.save()
# But there is still no gathering witness => nothing can bee seen in GC :(
# Presumably a gathering belong and gathering witness are needed also?

# all regid's seem to have the same gathering_id in table action_gathering_belong 
# assuming this is the case, find the gathering_id of any gathering in the current location
  gathering_id = None
  try:
    gatheringobj = Gathering.objects.filter(location__id=locid).first()
    
    print("gatheringobj=", gatheringobj)
    if gatheringobj != None and gatheringobj.regid != "":
      gatheringbelong = Gathering_Belong.objects.filter(regid=gatheringobj.regid).first()
      print("gatheringbelong=", gatheringbelong)
      gathering_id = gatheringbelong.gathering_id
      
      print("gatheringid=", gathering_id)
      print("gathering object=", gathering)
      belong = Gathering_Belong(regid=gathering.regid, gathering=gatheringobj)
      print("saving belong")
      belong.save()
      witness = Gathering_Witness()
      witness.gathering_id = gathering_id
      witness.date = datetime.datetime.strptime(request.POST.get('date'), '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)
      witness.save()
      print("saved witness with gathering_id=", gathering_id)
     
    print("gathering_id=", gathering_id)
  except Exception as e:
    print("Exception:",e)
  

  print(f"GUPG {gathering.__dict__}")
  return redirect('action:geo_view', locid)

def geo_search(request):
  locid = request.POST.get('location')
  return redirect('action:geo_view', locid)

def geo_invalid(request, error_message = None):
  template = loader.get_template('action/geo_invalid.html')
  context = {
    'error_message': error_message
  }
  return HttpResponse(template.render(context, request))

def handle_favorite(request, locid):
  #print(f"FAVH {locid}")
  if request.user.is_authenticated:
    #print(f"FAVX Authenticated")
    userhome = UserHome.objects.get(callsign=request.user.username)
    #print(f"FAVU {request.user.username}")
    gathering = Gathering.objects.filter(location=locid).first()
    if userhome.favorite_locations.filter(id=gathering.location.id).count() == 0:
      #print(f"FAVA {gathering.location.id}")
      userhome.favorite_locations.add(gathering.location.id)
    else:
      #print(f"FAVR {gathering.location.id} {UserHome.objects.filter(favorite_locations__id=gathering.location.id)} {UserHome.favorite_locations.__dict__}")
      userhome.favorite_locations.remove(gathering.location.id)
    userhome.save()
    #print(f"FAVS Saved {UserHome.favorite_locations} {UserHome.objects.filter(favorite_locations__id=gathering.location.id)}")

def translate_maplink(request, regid, date):
  #print(f"RRRC {regid, date}")
  try:
    gathering_belong = Gathering_Belong.objects.filter(regid=regid).first()
    gathering = Gathering.objects.filter(regid=gathering_belong.gathering).first()
    locid = gathering.location.id
    #print(f"RRRS '{regid}' --> '{locid}'")
    return redirect('action:geo_view', locid=locid)
  except:
    #print(f"RRRF")
    return redirect('action:geo_invalid')
