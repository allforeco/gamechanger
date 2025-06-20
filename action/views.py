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
from django.shortcuts import render, redirect
from django.template import loader, RequestContext
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms import ModelForm
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
#from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from django import forms
from django.db.models import Sum
from django.contrib.auth.models import User
from dal import autocomplete
try:
  from action.spooler import action_spooler
except:
  from action.spooler import action_nospooler, update_reg
  action_spooler = None
  print(f"SIMP No uwsgi spooler environment")

import datetime, io, csv, os, traceback, threading, html, base64, hashlib, json
import googlemaps

from .bigredbutton import BigRedButton
from . parsers import geoParser, MediaParser
from .models import Gathering, Gathering_Belong, Gathering_Witness, Location, UserHome, Organization, Country
from .map_sync import eventmap_data_view, eventmap_data, coffer_data, to_fff
from .tools_view import tools_view_handler, tools_view_post
from .geo_view import geo_view_handler, geo_date_view_handler, geo_update_view, geo_update_post, geo_search, geo_invalid, translate_maplink, geo_view_handler_new, AF_mark_as_duplicate, geo_one_more_view
from .start_view import start_view_handler
from .overview_view import latest_records_view, help_view
from .locations_view import locations_view
from. contacts_view import contacts_view, contacts_import
from .organizations_view import organizations_view, organization_view
from .gathering_view import gathering_view
from .user_createsubmitform_view import USGCreate, USGCreateSubmit, GatheringCreate, GatheringCreateSubmit, OrganizationcontactCreate, OrganizationcontactCreateSubmit, OrganizationCreate, OrganizationCreateSubmit, LocationCreate, LocationCreateSubmit
from .cookie_profile import CookieProfile, loginCookieProfile
from .crypto import Crypto

import datetime

'''UNUSED
???gathering formclass
'''
class GatheringSearch(FormView):
  class GatheringSearchForm(forms.ModelForm):
    #class Meta:
    #  model = Gathering
    #  fields = ['gathering_type', 'location', 'start_date']
    #  print(f"GSF1 ")
    #  widgets = {
    #    'location': autocomplete.ModelSelect2(url='/action/location-autocomplete/')
    #  }
    def get_success_url(self):
      return reverse_lazy('action:overview', kwargs={'regid': '11111111'})
  template_name = 'action/gathering_search.html'
  form_class = GatheringSearchForm
  success_url = '/thanks/'

  def form_valid(self, form):
    return super().form_valid(form)

'''
???user home view
'''
class HomeView(FormView):
  class LocationSearchForm(forms.Form):
    #class InLocationChoiceFieldDecorator(forms.ModelChoiceField):
    #  def label_from_instance(self, obj):
    #    return f"<<{obj.name}>>"

    #location = InLocationChoiceFieldDecorator(
    location = forms.ModelChoiceField(
      queryset=Location.objects.all(),
      widget=autocomplete.ModelSelect2(
        url='/action/location-autocomplete/',
        attrs={'data-minimum-input-length': 3}),
      label='Select Particular',
      #label_from_instance=lambda obj:f"<<<{obj.name}>>>",
      required=False,
    )
    #freetext = forms.CharField(
    #  label='Freetext Search',
    #  required=False)

  template_name = 'action/home.html'
  form_class = LocationSearchForm

  def get_success_url(self):
    print(f"HOMS {self.clean_location}")
    try:
      return reverse_lazy('action:geo_view', kwargs={'locid': self.clean_location.id})
    except:
      return reverse_lazy('action:home')

  def form_valid(self, form):
    self.clean_location = form.cleaned_data.get('location')
    self.clean_freetext = form.cleaned_data.get('freetext')
    if not self.clean_location:
      self.clean_location = self.clean_freetext
    print(f"HOMV {self.clean_location}")
    return super().form_valid(form)

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    print(f"HOMC {context}")
    favorites_list = []
    recents_list = []
    userhome = None
    template = loader.get_template('action/home.html')

    if self.request.user.is_authenticated:
      try:
        userhome = UserHome.objects.get(callsign=self.request.user.username)
        favorites_list = []
        for loc in userhome.favorite_locations.all():
          locid = Gathering.objects.filter(location=loc).first().location_id
          regid = Gathering.objects.filter(location=loc).first().regid
          events = [w.participants for w in Gathering_Witness.objects.filter(gathering=regid)]
          last_week = [w.participants for w in Gathering_Witness.objects.filter(gathering=regid, 
            date__gte=datetime.date.today()-datetime.timedelta(days=7))]
          favorites_list += [{
            "name": loc.name, 
            "events": len(events), 
            "participants": sum(events),
            "last_week": sum(last_week),
            "regid": regid,
            "locid": locid,
            "in_location": loc.in_location,
          }]
          print(f"HOM2 {loc.name} in {loc.in_location}")
      except:
        print(f"HOMF No userhome object for user {self.request.user.username}")
        userhome = None

    context = {
      'userhome': userhome,
      'visibility': userhome.get_visibility_str() if userhome else None,
      'error_message': '',
      'favorites_list': favorites_list,
      'recents_list': recents_list,
      **context,
    }
    return context

'''
___autocomplete widget, Location
'''
class LocationAutocomplete(autocomplete.Select2QuerySetView):
  def get_queryset(self):
    #print(f"AUTL Entered")
    #qs = Location.objects.exclude(in_country=Country.objects.get(id=-1)).order_by('name') #qs = Location.objects.all().order_by('name')
    #print(f"AUTL {len(qs)} locations")
    #if self.q:
    #  qs = qs.filter(name__icontains=self.q)
    #  #qs = qs.filter(name__icontains=self.q).exclude(name__icontains=", ")
    #return qs
    return Location.search(self.q)
  
class CountryAutocomplete(autocomplete.Select2QuerySetView):
  def get_queryset(self):
    return Country.search(self.q)

class LocationCountryFilter(autocomplete.Select2QuerySetView):
  def get_queryset(self):
    locations = Location.objects.exclude(in_country=Country.Unknown())
    country = self.forwarded.get('country', None)

    if self.q:
      locations = Location.search(self.q)

    if country:
      locations = locations.filter(in_country=country).order_by('name')

    return locations

'''
___autocomplete widget, Organization
'''
class OrganizationAutocomplete(autocomplete.Select2QuerySetView):
  def get_queryset(self):
    #print(f"AUTO Entered")
    ##if not self.request.user.is_authenticated:
    ##  return Organization.objects.none()
    #qs = Organization.objects.all()
    #print(f"AUTO {len(qs)} organizations")
    #if self.q:
    #  qs = qs.filter(name__icontains=self.q)
    #return qs
    return Organization.search(self.q)


'''
___calculate gathering regid
___by time & email (unsustainable)
'''
def rid_generator(rtime, cemail):
  if not(rtime) or not(cemail):
    return
  return base64.urlsafe_b64encode(hashlib.md5(str(rtime+':'+cemail).encode()).digest()).decode()[:8]

'''
???
'''
def spool_update_reg(response_file_bytes):
  print(f"INIT uwsgi req {len(response_file_bytes)}")
  action_spooler.spool(task=b'upload', body=response_file_bytes)
  print(f"INIT uwsgi spooled")

'''
???
'''
def nospool_update_reg(response_file_bytes):
  print(f"INIT nospool req {len(response_file_bytes)}")
  action_nospooler(response_file_bytes.decode('utf8'))
  #update_reg(str(response_file_bytes).split("\n"), "last_import.log")
  print(f"INIT nospool done")

'''
???
'''
def get_canonical_regid(regid):
  try:
    canonical_regid = Gathering_Belong.objects.filter(regid=regid).first().gathering.regid
    return canonical_regid
  except Exception as ex:
    count_regid = Gathering_Belong.objects.filter(regid=regid).count()
    print(f"GCRN {count_regid} canonical regid for '{regid}': {ex}")
    return None

'''?DEPRICATED
???
'''
def index(request):
  return redirect('action:start')
  latest_gathering_list = Gathering_Witness.objects.order_by('-creation_time')[:5]
  template = loader.get_template('action/index.html')
  context = {
    'latest_gathering_list': latest_gathering_list,
  }
  return HttpResponse(template.render(context, request))

'''
???
'''
def overview_by_name(request):
  loc_name = request.GET.get('location','')
  loc_exact = request.GET.get('exact','')
  loc_id = request.GET.get('locid','')
  return _overview_by_name(request, loc_name, loc_exact, loc_id)

'''
???
'''
def bad_link(request, error_message):
  context = {
    'error_message': error_message,
  }
  template = loader.get_template('action/bad_link.html')
  return HttpResponse(template.render(context, request))

'''
???
'''
def _overview_by_name(request, loc_name='', loc_exact='', loc_id=''):
  if not loc_name and not loc_id:
    return bad_link(request, "Something went wrong with this link (#11)")

  locations = []
  max_entries = 100
  sublocations = []
  sublocation_parent = None
  if loc_id:
    location_list = Location.objects.filter(id=int(loc_id))
  elif loc_exact:
    location_list = Location.objects.filter(name=loc_name)
  else:
    if "," not in loc_name:
      # Simple search for a name
      location_list = Location.objects.filter(name__icontains=loc_name)
    else:
      # Name is something like "Colorado Blvd, Denver, CO, USA"
      loc_name = Location.make_location_name(*Location.split_location_name(loc_name))
      location_levels = [name.strip() for name in loc_name.split(",")]
      loc_name = location_levels[0]
      print(f"CLS0 loc_name {loc_name}")
      cand_locations = Location.objects.filter(name__icontains=loc_name)
      location_list = []
      print(f"CLS1 {len(cand_locations)} to be matched against {location_levels}")
      for cand_location in cand_locations:
        # Only spend CPU time searching if there is any hope of a match
        print(f"CLSS -- {cand_location.name} --")
        is_candidate = True
        in_area = cand_location
        loc_in_list = location_levels
        watchdog = 8
        while loc_in_list:
          watchdog -= 1
          if watchdog < 0:
            print(f"CLSX {loc_in_list}")
            break
          print(f"CLST - {loc_in_list} -")
          if loc_in_list[0] in in_area.name:
            print(f"CLS2 {loc_in_list[0]} passed {in_area.name}")
            loc_in_list = loc_in_list[1:]
            continue
          if in_area == cand_location.in_location:
            print(f"CLSY still on {cand_location.in_location.name}")
          in_area = in_area.in_location
          if not in_area:
            is_candidate = False
            print(f"CLS4 no more parent areas")
            break
          print(f"CLS3 try parent area {in_area.name}")
        if not loc_in_list:#is_candidate:
          print(f"CLS5 candidate added {cand_location.name} in {in_area}")
          for parent_loc_name in [name.strip() for name in cand_location.name.split(",")]:
            parent_loc = Location.objects.filter(name=parent_loc_name).first()
            if parent_loc:
              sublocation_parent = parent_loc
              break
          print(f"CLS6 {sublocation_parent} taken from {cand_location.name}")

          if "," in cand_location.name and not cand_location.in_location:
            # This candidate location is not a country, and does not have a parent. Skip.
            print(f"CLS7 Disqualified {cand_location.name}")
            continue

          location_list += [cand_location]
      print(f"CLS9 location_list {location_list}")

  location_list = [loc for loc in location_list if loc.in_location or "," not in loc.name]
  print(f"OVLC count {location_list}")
  if len(location_list) == 1:
    print(f"OVL1 {location_list[0]}")
    sublocation_parent = location_list[0]
  if sublocation_parent:
    print(f"OVLP {sublocation_parent}")
    sublocations = list(Location.objects.filter(in_location=sublocation_parent).order_by('name'))

  if len(location_list) == 1:
    print(f"OVBN shortcut {loc_name}")
    return redirect('action:geo_view', location_list[0].id)

  locations = []
  for loc in location_list:
    locations += [{
        'name':html.escape(loc.name), 
        'in_location': loc.in_location, 
        'locid': loc.id,
      }]

  truncated = None
  if len(locations) == max_entries:
    truncated = f"... (search limited to {max_entries} results) ..."
  locations.sort(key=lambda e: e['name'])

  context = {
    'error_message': '',
    'locations': locations,
    'truncated': truncated,
    'sublocation_parent': sublocation_parent,
    'sublocations': sublocations,
  }
  template = loader.get_template('action/location_overview.html')
  return HttpResponse(template.render(context, request))

'''
???
'''
def upload_reg(request, error_message=None):
  context = {
    'error_message': error_message,
  }
  template = loader.get_template('action/upload_reg.html')
  return HttpResponse(template.render(context, request))

'''
???
'''
@csrf_exempt
def upload_post(request):
  try:
    token = request.POST['token']
    regfile = request.FILES['regfile']
  except KeyError:
    # Redisplay the form
    return upload_reg(request, error_message="You must specify a RegID file")

  if token != os.environ['GAMECHANGER_UPLOAD_TOKEN']:
    return upload_reg(request, error_message="You must specify a valid RegID file")

  response_file_bytes = regfile.read()

  print(f"UPSP Spooling len {len(response_file_bytes)} sample {str(response_file_bytes)[:100]}...")
  try:
    spool_update_reg(response_file_bytes)
  except Exception as e:
    print(f"Spooling exception {e}")
    print(f"NOSpooler solution {len(response_file_bytes)}")
    nospool_update_reg(response_file_bytes)
    
  print(f"UPSD Spooled {len(response_file_bytes)} bytes")
  return upload_reg(request, error_message=f"{len(response_file_bytes)} bytes successfully uploaded")

'''
???
'''
def download_upd(request, error_message=None):
  context = {
    'error_message': error_message,
  }
  template = loader.get_template('action/download_upd.html')
  return HttpResponse(template.render(context, request))

'''
???
'''
@csrf_exempt
def download_post(request):
  try:
    token = request.POST['token']
    start_datetime = request.POST['start_datetime']
  except KeyError:
    # Redisplay the form
    return download_upd(request, error_message="You must specify a start date and time")

  if token != os.environ['GAMECHANGER_UPLOAD_TOKEN']:
    return download_upd(request, error_message="You must specify a valid start date and time")

  try:
    #comment = '''
    t = datetime.datetime.fromisoformat(start_datetime+"+00:00")
    # Order so that most recently updated data comes last, i.e. overwrites earlier data
    gatherings = Gathering.objects.filter(updated_on__gte=t).order_by('updated_on')
    print(f"GUD0 cnt {len(gatherings)}")
    witnesses = Gathering_Witness.objects.filter(updated__gte=t).order_by('updated')
    print(f"GUD1 cnt {len(witnesses)}")
    witness_dates = {}
    for witness in witnesses:
      try:
        witness_dates[(witness.gathering.regid, witness.date)] = 1
      except:
        print(f"GUD2 missing witness regid/date for {witness}")

    with io.StringIO(newline='') as csvfile:
      content = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
      for gathering in gatherings:
        if witness_dates.get((gathering.regid, gathering.start_date)):
          # Don't mention a Gathering and Witness for the same date
          print(f"GUD3 not mentioning {(gathering.regid, gathering.start_date)}")
          continue
        content.writerow([
          'CG',                             # 0 Record format
          gathering.regid,                  # 1 RID
          gathering.created_on or gathering.start_date, # 2 RCREATED
          gathering.updated_on or gathering.start_date, # 3 RUPD
          gathering.start_date,             # 4 EDATE
          gathering.end_date,               # 5 EENDDATE
          gathering.time,                   # 6 ETIME
          gathering.address,                # 7 ELOCATION
          gathering.location.in_country.name, # 8 ECOUNTRY
          gathering.location.canonical_name(), # 9 GLOC
          gathering.location.lat,           # 10 GLAT
          gathering.location.lon,           # 11 GLON
          gathering.gathering_type,         # 12 ETYPE
          gathering.event_link_url,         # 13 ELINK
          "|".join([org.name for org in gathering.organizations.all()]), # 14 CORG2
          gathering.contact_email,          # 15 CEMAIL
          gathering.expected_participants,  # 16 REVNUM
          "",                               # 17 REVPROOF
          gathering.coordinator,            # 18 SCOORD
          gathering.steward,                # 19 SSTEWARD
          gathering.guide,                  # 20 SGUIDE
        ])

      for witness in witnesses:
        gathering = None
        try:
          try:
            bels = Gathering_Belong.objects.filter(regid=witness.gathering.regid)
            bel = bels.first()
            gathering = bel.gathering
          except:
            pass
          if not gathering:
            print(f"GUD8 missing belong for {witness.gathering.regid}")
            gathering = witness.gathering
          if witness.gathering.regid != gathering.regid:
            print(f"GUD9 belong {witness.gathering.regid} => {gathering}")
          content.writerow([
            'CGW',                            # 0 Record Format
            gathering.regid,                  # 1 RID
            witness.creation_time,            # 2 RCREATED
            witness.updated,                  # 3 RUPD
            witness.date,                     # 4 EDATE
            witness.date,                     # 5 EENDDATE
            gathering.time,                   # 6 ETIME
            gathering.address,                # 7 ELOCATION
            gathering.location.in_country.name, # 8 ECOUNTRY
            gathering.location.canonical_name(), # 9 GLOC
            gathering.location.lat,           # 10 GLAT
            gathering.location.lon,           # 11 GLON
            gathering.gathering_type,         # 12 ETYPE
            gathering.event_link_url,         # 13 ELINK
            witness.organization.name if witness.organization else "", # 14 CORG2
            gathering.contact_email,          # 15 CEMAIL
            witness.participants,             # 16 REVNUM
            witness.proof_url,                # 17 REVPROOF
            witness.coordinator,              # 18 SCOORD
            witness.steward,                  # 19 SSTEWARD
            witness.guide,                    # 20 SGUIDE
          ])
        except Exception as e:
          print(f"GUDX {e}")
      
          #rtime ?|creattime
          #rsource |'Gamechanger'
          #CMAIL |gathering.contact_mail / defmail
          #CNAME |gathering.contact_name
          #CORG2 |organization
          #CSPOKE ?| private / public
          #ECOUNTRY x|gathering.location.country_location()
          #ECITY x|gathering.location.city
          #ELOCATION |gathering.location
          #ETYPE |gathering.gathering_type
          #ETIME |gathering.time
          #EFREQ %|gathering.end_date "weekly" / "once only" [def] / "every friday"
          #ELINK ?| (Event Invite)
          #GLOC x|gathering.location.gloc (google name)
          #GlAT |gathering.location.lat
          #GLON |gathering.location.lon
      return HttpResponse(csvfile.getvalue(), content_type="text/plain")
    #  '''
    #return HttpResponse(coffer_data(), content_type="text/plain")
  except Exception as e:
    print(f"DPXX Download exception: {e}")
    return download_upd(request, error_message="Download failed")

'''
???
'''
def join_us(request):
  error_message=None
  context = { 'error_message': error_message }
  template = loader.get_template('action/join_us.html')
  if error_message or not request.POST.get('screenname'):
    return HttpResponse(template.render(context, request))
  raw_invitation_code = request.POST['invitation_code']
  if "🐥" not in raw_invitation_code:
    context = {'error_message': f"This invitation code is fake, expired or already used. Please ask your inviter for a new one."}
    return HttpResponse(template.render(context, request))
  raw_screenname = request.POST['screenname']
  if " " in raw_screenname:
    context = {'error_message': f"No spaces in the Callsign, please."}
    return HttpResponse(template.render(context, request))
  if len(raw_screenname) < 5:
    context = {'error_message': f"Pick a longer Callsign, please. At least 5 characters."}
    return HttpResponse(template.render(context, request))
  max_length = UserHome._meta.get_field('callsign').max_length
  if len(raw_screenname) > 25:
    context = {'error_message': f"Pick a shorter Callsign, please."}
    return HttpResponse(template.render(context, request))

  password = request.POST['password']
  if len(password) < 10:
    context = {'error_message': f"Please pick a longer password."}
    return HttpResponse(template.render(context, request))

  visibility = request.POST['visibility']
  if visibility not in [UserHome.CALLSIGN, UserHome.PRIVATE, UserHome.FRIENDS, UserHome.PUBLIC, UserHome.OPENBOOK]:
    context = {'error_message': f"Please select your desired visibility level."}
    return HttpResponse(template.render(context, request))

  screenname = html.escape(raw_screenname)
  callsign = html.escape(raw_screenname.lower())
  if UserHome.objects.filter(callsign=callsign):
    context = {'error_message': f"Callsign '{screenname}' is already taken. Please try another one."}
    return HttpResponse(template.render(context, request))

  try:
    loginuser = User(username = callsign)
    loginuser.set_password(password)
    loginuser.save()
  except Exception as e:
    loginuser = User.objects.get(username=callsign)
    print(f"JOIX Login user creation exception: {e}")

  userhome = UserHome(
    callsign = callsign, 
    screenname = screenname,
    loginuser_id = loginuser.id,
    visibility_level = visibility,
  )
  userhome.save()
  context = {'error_message': f"Callsign '{screenname}' successfully created."}
  return HttpResponse(template.render(context, request))

# Generate a new key by navigating to
# https://staging.gamechanger.eco/action/crypto?regen=xxx
# https://www.gamechanger.eco/action/crypto?regen=xxx
# Unlock a key by navigating to
# https://staging.gamechanger.eco/action/crypto?unlock=xxx
# https://www.gamechanger.eco/action/crypto?unlock=xxx
def crypto_view(request, error_message=None):
  known_keys = Crypto.get_known_keys(request.COOKIES)
  abs_base = None
  unlock = request.GET.get('unlock', None)
  if unlock:
    [num, key] = unlock.split(':')
  else:
    token = os.environ.get('GAMECHANGER_CRYPTO_TOKEN')
    if token and request.GET.get('regen', None) == token:
      # Generate keypair
      (num, key) = Crypto.gen_privkey_as_urlstr()
      abs_base = request.build_absolute_uri('')
    else:
      num = ""
      key = ""

  context = {
    'error_message': error_message,
    'unlock': unlock,
    'cookie_num': num,
    'cookie_key': key,
    'abs_base': abs_base,
    'known_keys': ', '.join(known_keys),
  }
  template = loader.get_template('action/crypto.html')
  response = HttpResponse(template.render(context, request))
  if unlock:
    response.set_cookie(
      f'gc_key_{num}', key,
      max_age = datetime.timedelta(days=100),
      secure=True,
      httponly=True,
      samesite='Strict',
    )
  return response

def emergency_activate(request):
  if request.user.is_authenticated:
    print("brb:", BigRedButton.is_emergency())
    BigRedButton.emergency_activate()
    print("brb:", BigRedButton.is_emergency())
  return redirect('action:start')

def emergency_deactivate(request):
  if request.user.is_authenticated:
    print("brb:", BigRedButton.is_emergency())
    BigRedButton.emergency_deactivate()
    print("brb:", BigRedButton.is_emergency())
  return redirect('action:start')

'''
'''
def permission_denied(request):
  context = {}
  template = loader.get_template('action/permission_denied.html')
  return HttpResponse(template.render(context, request))

'''
???
'''
def bad_request(request, exception):
    print(f"H400 {request}")
    return render(request, 'action/400.html', status=400)

'''
???
'''
def permission_denied(request, exception):
    print(f"H403 {request}")
    return render(request, 'action/403.html', status=403)

'''
???
'''
def page_not_found(request, exception):
    print(f"H404 {request}")
    return render(request, 'action/404.html', status=404)

'''
???
'''
def server_error(request):
    print(f"H500 {request}")
    traceback.print_exc()
    return render(request, 'action/500.html', status=500)
