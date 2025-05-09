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
#from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from django import forms
from .models import Gathering, Gathering_Belong, Gathering_Witness, Location, Location_Belong, UserHome, Organization, Coordinator, Steward, Guide
from .crypto import Crypto
from django.shortcuts import redirect
import datetime

'''
===Handle location viewing
'''

'''
???
'''
def geo_view_handler(request, locid):
  #print(f"TOWH {locid}")
  #LOCATION
  if not Location.Duplicate_is_prime(Location.objects.filter(id=locid).first()):
    return redirect('action:geo_view',Location.Duplicate_get_prime(Location.objects.filter(id=locid).first()).id)
  this_location = Location.objects.filter(id=locid).first()
  if not (this_location):
    return redirect('action:geo_invalid')

  parent_location = this_location.in_location
  sublocation_list_raw = Location.objects.filter(in_location=this_location).order_by('name')
  sublocation_list = Location.objects.none()
  for sl in sublocation_list_raw:
    if Location.Duplicate_is_prime(sl):
      sublocation_list |= Location.objects.filter(id=sl.id)
  sublocation_list = sublocation_list.order_by('name')

  event_head = Gathering.datalist_template(
    date=True, recorded=True,model=True,record=True, 
    location=True, map_link=True, participants=True, 
    gtype=True, orgs=True, 
    event_link=True, recorded_link=True,
    coordinator=True, steward=True, guide=True)
  event_list = []
  #GATHERING
  gathering_list = Gathering.objects.filter(location=this_location).order_by('-start_date')
  #for sl in sublocation_list:
  #  gathering_list |= Gathering.objects.filter(location=sl)

  event_list = Gathering_Witness.get_witnesses(gathering_list, event_head)
  event_list.sort(key=lambda e: e['date'], reverse=True)

  for index, e in enumerate(event_list):
    if not e.get('future', False):
      if index:
        e['separator'] = True
      break

  total_participants = sum([w['participants'] for w in event_list if 'participants' in w and w['participants']])
  template = loader.get_template('action/geo_view.html')
  try:
    favorite_location = UserHome.objects.get(callsign=request.user.username).favorite_locations.filter(name=this_location.name).exists()
  except:
    favorite_location = False

  context = {
    'this_location': this_location,
    'parent_location': parent_location,
    'sublocation_list': sublocation_list,
    'event_head': event_head,
    'event_list': event_list,
    'total_participants': total_participants,
    'favorite_location': favorite_location,
    'root_gathering': [],#FIXME witness_list[0].gathering if witness_list else [],
    'gathering_types': Gathering.gathering_type.field.choices,
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

'''
???
'''
def geo_view_handler_new(request, locid):
    # print(f"TOWH {locid}")
    if not Location.Duplicate_is_prime(Location.objects.filter(id=locid).first()):
      return redirect('action:geo_view_new', Location.Duplicate_get_prime(Location.objects.filter(id=locid).first()).id)
    this_location = Location.objects.filter(id=locid).first()
    if not (this_location):
        return redirect('action:geo_invalid')

    parent_location = this_location.in_location
    sublocation_list_duplicates = Location.objects.filter(in_location=this_location).order_by('name')
    sublocation_list = Location.objects.none()
    for sl in sublocation_list_duplicates:
      if Location.Duplicate_is_prime(sl):
        sublocation_list |= Location.objects.filter(id=sl.id)
    sublocation_list = sublocation_list.order_by('name')
    #sublocation_list = Location.objects.filter(in_location=this_location).order_by('name')
    gathering_loc = Gathering.objects.filter(location=this_location)
    witness_dict = {}
    # print(f"TOWH {this_location} {parent_location} {len(sublocation_list)} {len(gathering_loc)}")
    for gathering in gathering_loc:
        raw_witness_list = list(Gathering_Witness.objects.filter(gathering=gathering))
        # print(f"TOWI {gathering} {len(raw_witness_list)} {raw_witness_list}")
        for w in raw_witness_list:
            belong_regid = w.set_gathering_to_root()
            witness_dict[(belong_regid, w.date)] = w
            # print(f"TOWD {(belong.gathering.regid,w.date)} = {w}")
    witness_list = list(witness_dict.values())
    witness_list.sort(key=lambda e: e.date, reverse=True)
    total_participants = sum([w.participants for w in witness_list if w.participants])

    # Create a list of active gatherings
    gathering_list_raw = list(Gathering.objects.filter(location=this_location,
                                                       end_date__gte=datetime.datetime.today() - datetime.timedelta(days=7)) \
                              .only("location", "start_date", "end_date", "time", "address", "organizations", "expected_participants"))
    gathering_dict = {}
    for g in gathering_list_raw:
        gathering_dict[g.regid] = {
            "location": g.location,
            "start_date": g.start_date,
            "end_date": g.end_date,
            "time": g.time,
            "address": g.address,
            "organization": None,
            "expected_participants": g.expected_participants
        }
        if len(g.organizations.all()) > 0:
            gathering_dict[g.regid]["organization"] = g.organizations.all()[0]
    gathering_list = list(gathering_dict.values())

    try:
        favorite_location = UserHome.objects.get(callsign=request.user.username).favorite_locations.filter(
            name=this_location.name).exists()
    except:
        favorite_location = False

    context = {
        'this_location': this_location,
        'parent_location': parent_location,
        'sublocation_list': sublocation_list,
        'witness_list': witness_list,
        'total_participants': total_participants,
        'favorite_location': favorite_location,
        'root_gathering': witness_list[0].gathering if witness_list else [],
        'gathering_list': gathering_list
    }

    if request.POST.get('favorite'):
        # print(f"FAVV {request.POST.get('favorite')}")
        handle_favorite(request, this_location.id)

    if request.user.is_authenticated:
        # print(f"FAVU User {request.user.username}")
        try:
            userhome = UserHome.objects.get(callsign=request.user.username)
            gathering = Gathering.objects.filter(location=locid).first()
            context['favorite_location'] = str(
                gathering.location.id in [loc.id for loc in userhome.favorite_locations.all()])
            # print(f"FAVQ {context['favorite_location']} {gathering.location.id} {userhome.favorite_locations.all()}")
        except:
            # print(f"FAVF No userhome object for user {request.user.username}")
            userhome = None
    template = loader.get_template('action/geo_view_new.html')
    return HttpResponse(template.render(context, request))

'''
???
'''
def geo_date_view_handler(request, locid, date):
  print(f"TODH {locid} {date}")
  if not Location.Duplicate_is_prime(Location.objects.filter(id=locid).first()):
    return redirect('action:geo_date_view', Location.Duplicate_get_prime(Location.objects.filter(id=locid).first()).id, date)
  this_location = Location.objects.filter(id=locid).first()
  parent_location = this_location.in_location
  template = loader.get_template('action/geo_date_view.html')
  context = {
    'date': date,
    'this_location': this_location,
    'parent_location': parent_location,
  }
  return HttpResponse(template.render(context, request))

'''
???
'''
def geo_one_more_view(request):
  return geo_update_view(request, is_one_more = True)
'''
???
'''
def geo_update_view(request, is_one_more = False):
  is_gathering = (request.POST.get('is_gathering') == 'True')
  regid = request.POST.get('regid')
  witness_id = request.POST.get('witness')
  locid = request.POST.get('locid')
  orgid = request.POST.get('orgid')
  ghost_date = request.POST.get('ghost_date')
  next_url = request.POST.get('next_url')
  print(f"ghost_date={ghost_date}")
  print(f"REGID={regid}")
  print(f"POST1={request.POST}")
  print(f"next_url={next_url}")
  this_gathering = Gathering.objects.filter(regid=regid)
  if this_gathering:
    this_gathering = this_gathering.first()
  else:
    this_gathering = None
  if not witness_id or witness_id == 'None':
    this_witness = None
  else:
    this_witness = Gathering_Witness.objects.filter(id=witness_id)
    if this_witness:
      this_witness = this_witness.first()
    else:
      this_witness = None

  this_location = Location.objects.filter(id=locid)
  if this_location:
    this_location = this_location.first()
  try:
    print(f"Orgid {orgid}")
    print(f"Orgid {int(orgid)}")
    this_organization = Organization.objects.filter(id=int(orgid)).first()
  except:
    print(f"Orgid parsing exception")
    this_organization = None

  try:
    initial_weeks = (this_gathering.end_date - this_gathering.start_date).days // 7
  except:
    initial_weeks = 0

  if this_gathering and Crypto.is_encrypted(this_gathering.contact_name):
    this_gathering.contact_name = Crypto.decrypt_if_possible(this_gathering.contact_name, request.COOKIES)
  if this_gathering and Crypto.is_encrypted(this_gathering.contact_email):
    this_gathering.contact_email = Crypto.decrypt_if_possible(this_gathering.contact_email, request.COOKIES)
    email_visible = False
  else:
    email_visible = True
  if this_gathering and Crypto.is_encrypted(this_gathering.contact_phone):
    this_gathering.contact_phone = Crypto.decrypt_if_possible(this_gathering.contact_phone, request.COOKIES)

  context = { 
    'is_one_more': is_one_more,
    'is_gathering': is_gathering,
    'location': this_location,
    'organization': this_organization,
    'gathering_types': Gathering.gathering_type.field.choices,
    'stewards': Steward.objects.all(),
    'initial_weeks': initial_weeks,
    'email_visible': email_visible,
    'ghost_date': ghost_date,
    'next_url': next_url,
  }
  if this_gathering: context['gathering'] = this_gathering
  if this_witness: context['witness'] = this_witness

  template = loader.get_template('action/geo_update_view.html')
  return HttpResponse(template.render(context, request))

'''
???
'''
def geo_update_post(request):
  is_gathering = (request.POST.get('is_gathering') == 'True')
  if (is_gathering):
    return geo_update_post_gathering(request)
  else:
    return geo_update_post_witness(request)

'''
???
'''
def geo_update_post_witness(request):
  locid = request.POST.get('locid')
  regid = request.POST.get('regid')
  is_one_more = request.POST.get('is_one_more')
  if is_one_more in ["true", "True"]:
    witness_id = None # This is a new witness
  else:
    witness_id = request.POST.get('witness')

  do_delete_event = request.POST.get('do_delete_event')
  if do_delete_event:
    if request.user.is_authenticated:
      print(f"JKLD Delete {locid} : {regid} : {witness_id} by {request.user}")
      is_gathering = request.POST.get('is_gathering')
      if is_gathering == 'True':
        ...
        print(f"JKLD Deleted Gathering -- not implemented yet")
      else:
        witness = Gathering_Witness.objects.filter(pk=witness_id)
        witness.delete()
        print(f"JKLD Deleted Witness")
    else:
      print(f"JKLU Delete attempted by unauth user")
    return redirect('action:geo_view', locid)

  print(f"JKLO {locid} : {regid} : {witness_id}")

  gathering = Gathering.objects.get(regid=regid)
  if witness_id:
    witness = Gathering_Witness.objects.get(pk=witness_id)
  else:
    witness = Gathering_Witness(gathering=gathering)
  witness.gathering = gathering

  #RuntimeWarning: DateTimeField Gathering_Witness.updated received a naive datetime (2021-05-07 11:52:41.502616) while time zone support is active.
  witness.date = datetime.datetime.strptime(request.POST.get('date'), '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)
  witness.participants = request.POST.get('participants')
  witness.proof_url = request.POST.get('proof_url','')
  try:
    org = Organization.objects.get(id=request.POST.get('organization'))
    if org.name == 'None':
      org = None
    witness.organization = org
  except Exception as ex:
    witness.organization = None

  form_coordinator = request.POST.get('coordinator')
  print(f"GS {gathering.coordinator.pk if gathering.coordinator else None} WS {witness.coordinator.pk if witness.coordinator else None} FS {form_coordinator}")
  if form_coordinator:
    if gathering.coordinator and gathering.coordinator.pk == int(form_coordinator):
      witness.coordinator = None
    else:
      witness.coordinator = Steward.objects.get(pk=form_coordinator)
  else:
    witness.coordinator = None
  print(f"WGCU Witness coordinator updated GS {gathering.coordinator} WS {witness.coordinator} FS {form_coordinator}")

  form_steward = request.POST.get('steward')
  print(f"GS {gathering.steward.pk if gathering.steward else None} WS {witness.steward.pk if witness.steward else None} FS {form_steward}")
  if form_steward:
    if gathering.steward and gathering.steward.pk == int(form_steward):
      witness.steward = None
    else:
      witness.steward = Steward.objects.get(pk=form_steward)
  else:
    witness.steward = None
  print(f"WGSU Witness steward updated GS {gathering.steward} WS {witness.steward} FS {form_steward}")

  form_guide = request.POST.get('guide')
  print(f"GS {gathering.guide.pk if gathering.guide else None} WS {witness.guide.pk if witness.guide else None} FS {form_guide}")
  if form_guide:
    if gathering.guide and gathering.guide.pk == int(form_guide):
      witness.guide = None
    else:
      witness.guide = Steward.objects.get(pk=form_guide)
  else:
    witness.guide = None
  print(f"WGGU Witness guide updated GS {gathering.guide} WS {witness.guide} FS {form_guide}")

  witness.updated = datetime.datetime.today().replace(tzinfo=datetime.timezone.utc)
  witness.save()

  print(f"GUPW {witness.__dict__}")
  next_url = request.POST.get('next_url')
  if next_url:
    print(f"next_url {next_url}")
    return redirect(next_url)
  return redirect('action:geo_view', locid)

'''
???
'''
def geo_update_post_gathering(request):
  locid = request.POST.get('locid')
  regid = request.POST.get('gathering')
  print(f'POST2={request.POST}')
  if regid:
    gathering = Gathering.objects.filter(pk=regid).first()
    print(f'GUPD Found gathering {gathering}')
  else:
    gathering = Gathering()
    gathering.regid = Gathering.generate_regid()
    print(f'GUPD New gathering {gathering}')
  gathering.location = Location.objects.filter(pk=locid).first()
  gathering.start_date = datetime.datetime.strptime(request.POST.get('date'), '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)
  weeks = int(request.POST.get('weeks'))
  gathering.end_date = gathering.start_date + datetime.timedelta(weeks=weeks)
  gathering.expected_participants = request.POST.get('participants')
  gathering.gathering_type = request.POST.get('gathering-type')

  gathering.event_link_url = request.POST.get('event_link')

  #gathering.duration = request.POST.get('duration')
  gathering.address = request.POST.get('address')
  gathering.time = request.POST.get('time')

  crdid = request.POST.get('coordinator')
  if crdid:
    gathering.coordinator = Steward.objects.get(pk=crdid)
  else:
    gathering.coordinator = None

  stwid = request.POST.get('steward')
  if stwid:
    gathering.steward = Steward.objects.get(pk=stwid)
  else:
    gathering.steward = None

  gdeid = request.POST.get('guide')
  if gdeid:
    gathering.guide = Steward.objects.get(pk=gdeid)
  else:
    gathering.guide = None

  cname = request.POST.get('contact_name')
  if Crypto.is_cleartext(cname):
    print(f"CNAME {cname}")
    gathering.contact_name = Crypto.encrypt_with_markup(cname)
    print(f"GACNA {cname}")
    print(f"CLEAR {Crypto.decrypt_if_possible(cname,request.COOKIES)}")
    print(f"DECRY {Crypto.decrypt_if_possible(gathering.contact_name,request.COOKIES)}")

  cemail = request.POST.get('contact_email')
  if cemail and Crypto.is_cleartext(cemail):
    if request.POST.get('visibility') == 'yes':
      print('VISIBILITY Yes')
      gathering.contact_email = cemail
    else:
      print(f"VISIBILITY No {request.POST.get('visibility')}")
      gathering.contact_email = Crypto.encrypt_with_markup(cemail)
  
  cphone = request.POST.get('contact_phone')
  if Crypto.is_cleartext(cphone):
    gathering.contact_phone = Crypto.encrypt_with_markup(cphone)

  print(f"GUPG {gathering.__dict__}")
  gathering.save()
  belong = Gathering_Belong.objects.filter(regid = regid).first()
  if not belong:
    belong = Gathering_Belong(regid=regid, gathering=gathering)
    belong.save()

  # Must be done after gathering.save()
  try:
    orgid = request.POST.get('organization')
    print(f"GUP0 {orgid}")
    orgid = int(orgid)
    print(f"GUP1 {orgid}")
    organization = Organization.objects.get(pk=orgid)
    print(f"GUP2 {organization}")
    gathering.organizations.set([organization])
    print(f"GUP3 {gathering}")
    gathering.save()
    print(f"GUP4 Gathering saved")
  except Exception as e:
    print(f"GUPO <Organization:None> {e}")

  next_url = request.POST.get('next_url')
  if next_url:
    print(f"next_url {next_url}")
    return redirect(next_url)
  return redirect('action:geo_view', locid)

'''
???
'''
def geo_search(request):
  locid = request.POST.get('location')
  return redirect('action:geo_view', locid)

'''
???
'''
def geo_invalid(request, error_message = None):
  template = loader.get_template('action/geo_invalid.html')
  context = {
    'error_message': error_message
  }
  return HttpResponse(template.render(context, request))

'''
???
'''
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

'''
???
'''
def translate_maplink(request, regid, date):
  #print(f"RRRC {regid, date}")
  try:
    gathering_belong = Gathering_Belong.objects.filter(regid=regid).first()
    gathering = Gathering.objects.filter(regid=gathering_belong.gathering.regid).first()
    locid = gathering.location.id
    #print(f"RRRS '{regid}' --> '{locid}'")
    return redirect('action:geo_view', locid=locid)
  except:
    #print(f"RRRF")
    return redirect('action:geo_invalid')

def AF_mark_as_duplicate(request):
  prime = request.POST.get('prime')
  duplicate = request.POST.get('duplicate')
  lb = Location_Belong(duplicate=Location.objects.get(id=duplicate), prime=Location.objects.get(id=prime))
  lb.save()
  for gathering in Gathering.objects.filter(location=duplicate):
    gathering.location=Location.objects.get(id=prime)
    gathering.save()

  #for organizationcontact in organizationcontact
  return redirect('action:geo_view', locid=duplicate)