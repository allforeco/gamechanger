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

import datetime, io, csv, os, threading, html, base64, hashlib

from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms import ModelForm
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from django import forms
from django.db.models import Sum
from dal import autocomplete
try:
  from action.spooler import action_spooler
except:
  action_spooler = None
  print(f"SIMP No uwsgi spooler environment")
from .models import Gathering, Gathering_Belong, Gathering_Witness, Location, UserHome, Organization
from django.contrib.auth.models import User
from .geo_view import geo_view_handler, geo_date_view_handler, GeoUpdateView
from .start_view import start_view_handler
from .top_reporters_view import top_reporters_view_handler

class HomeView(FormView):
  class LocationSearchForm(forms.Form):
    location = forms.ModelChoiceField(
      queryset=Location.objects.all(),
      widget=autocomplete.ModelSelect2(
        url='/action/location-autocomplete/',
        attrs={'data-minimum-input-length': 3}),
      label='Select Particular',
      required=False,
    )
    freetext = forms.CharField(
      label='Freetext Search',
      required=False)

  template_name = 'action/home.html'
  form_class = LocationSearchForm

  def get_success_url(self):
    print(f"HOMS {self.clean_location}")
    return reverse_lazy('action:overview_by_name')+"?location="+str(self.clean_location)

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

class LocationAutocomplete(autocomplete.Select2QuerySetView):
  def get_queryset(self):
    print(f"AUTL Entered")
    if not self.request.user.is_authenticated:
      return Location.objects.none()
    qs = Location.objects.all()
    print(f"AUTL {len(qs)} locations")
    if self.q:
      qs = qs.filter(name__icontains=self.q)
    return qs

class OrganizationAutocomplete(autocomplete.Select2QuerySetView):
  def get_queryset(self):
    print(f"AUTO Entered")
    if not self.request.user.is_authenticated:
      return Organization.objects.none()
    qs = Organization.objects.all()
    print(f"AUTO {len(qs)} organizations")
    if self.q:
      qs = qs.filter(name__icontains=self.q)
    return qs

class GatheringSearch(FormView):
  class GatheringSearchForm(forms.ModelForm):
    class Meta:
      model = Gathering
      fields = ['gathering_type', 'location', 'start_date']
      print(f"GSF1 ")
      widgets = {
        'location': autocomplete.ModelSelect2(url='/action/location-autocomplete/')
      }
    def get_success_url(self):
      return reverse_lazy('action:overview', kwargs={'regid': '11111111'})
  template_name = 'action/gathering_search.html'
  form_class = GatheringSearchForm
  success_url = '/thanks/'

  def form_valid(self, form):
    return super().form_valid(form)

def rid_generator(rtime, cemail):
  if not(rtime) or not(cemail):
    return
  return base64.urlsafe_b64encode(hashlib.md5(str(rtime+':'+cemail).encode()).digest()).decode()[:8]

class GatheringCreate(FormView):
  class GatheringCreateForm0(forms.ModelForm):
    class Meta:
      model = Gathering
      fields = ['gathering_type', 'location', 'start_date', 'end_date', 'duration', 
        'expected_participants', 'organizations']
      print(f"GCV1 ")
      widgets = {
        'location': autocomplete.ModelSelect2(url='/action/location-autocomplete/'),
        'organizations': autocomplete.ModelSelect2(url='/action/organization-autocomplete/')
      }

    def get_success_url(self):
      return reverse_lazy('action:overview', kwargs={'regid': '11111111'})

    def form_valid(self, form):
      print(f"FORM valid")
      #form.send_email()
      return super().form_valid(form)

  class ActionGatheringCreateForm(forms.Form):
    location = forms.ModelChoiceField(#    FFF_GS_Dataformat.ELOCATION:
      queryset=Location.objects.all(),
      widget=autocomplete.ModelSelect2(
        url='/action/location-autocomplete/',
        attrs={'data-minimum-input-length': 3}),
      label='Location',
      required=True,
    )
    #FFF_GS_Dataformat.RTIME:   generated
    #FFF_GS_Dataformat.RSOURCE: Action.registration_source generated
    #FFF_GS_Dataformat.CEMAIL:  generated
    #FFF_GS_Dataformat.CNAME:   Action.creator User.name
    organization = forms.ModelChoiceField( #FFF_GS_Dataformat.CORG2:   item['CORG1'],
      queryset=Organization.objects.all(),
      widget=autocomplete.ModelSelect2(
        url='/action/organization-autocomplete/',
        #attrs={'data-minimum-input-length': 3}
      ),
      label='Organization',
      empty_label="(None)",
      required=False,
    )
    #FFF_GS_Dataformat.CSPOKE:  UserHome.visibility
    #FFF_GS_Dataformat.ECOUNTRY:Gathering.location.name derived
    #FFF_GS_Dataformat.ECITY:   Gathering.location.name
    gathering_type = forms.ChoiceField(label="Event Type", choices=Gathering._gathering_type_choices) #FFF_GS_Dataformat.ETYPE:   Gathering.gathering_type    
    gathering_start_time = forms.TimeField(label="Start Time") #FFF_GS_Dataformat.ETIME:
    gathering_start_date = forms.DateField(label="Start Date") #FFF_GS_Dataformat.EDATE:   Gathering.start_date
    gathering_duration = forms.DurationField(label="Duration")
    #gathering_frequency = forms.ModelChoiceField() #FFF_GS_Dataformat.EFREQ:   
    gathering_action_link = forms.URLField(label="Action URL", max_length=500) #FFF_GS_Dataformat.ELINK:   Action.action_link
    #FFF_GS_Dataformat.AAPPROVE:'y', generated based on Gathering_Witness(gathering=gathering, witness)
    #    FFF_GS_Dataformat.GLOC:    Gathering.location.name
    #    FFF_GS_Dataformat.GLAT:    Gathering.location.glat
    #    FFF_GS_Dataformat.GLON:    Gathering.location.glon

  template_name = 'action/gathering_form.html'
  form_class = ActionGatheringCreateForm
  #success_url = '/thanks/'

  def form_valid(self, form):
    self.form = form
    return super().form_valid(form)

  def get_success_url(self):
    self.callsign = UserHome.objects.get(loginuser_id=self.request.user.id).callsign
    print(f"AGCF {self.callsign}")
    self.rtime = str(datetime.datetime.now())
    self.cemail = self.callsign + "@gamechanger.eco"
    self.regid = rid_generator(self.rtime, self.cemail)
    print(f"AGCF {self.regid, self.form.__dict__}")
    print(f"AGCF {self.regid, self.form['gathering_start_date'].value()}")

    gathering = Gathering(
      regid=self.regid,
      gathering_type=self.form['gathering_type'].value(),
      location=Location.objects.get(id=self.form['location'].value()),
      start_date=self.form['gathering_start_date'].value(),
      end_date=self.form['gathering_start_date'].value())
    #print(f"Adding gathering {gathering}")
    gathering.save() 

    gathering_belong = Gathering_Belong(
      regid=self.regid,
      gathering=gathering)
    gathering_belong.save() 

    return reverse_lazy('action:report_date', kwargs={'regid': self.regid, 'date': self.form['gathering_start_date'].value()})

def spool_update_reg(response_file_bytes):
  print(f"INIT uwsgi req {len(response_file_bytes)}")
  action_spooler.spool(task=b'upload', body=response_file_bytes)
  print(f"INIT uwsgi spooled")

def get_canonical_regid(regid):
  try:
    canonical_regid = Gathering_Belong.objects.filter(regid=regid).first().gathering.regid
    return canonical_regid
  except Exception as ex:
    count_regid = Gathering_Belong.objects.filter(regid=regid).count()
    print(f"GCRN {count_regid} canonical regid for '{regid}': {ex}")
    return None

def index(request):
  latest_gathering_list = Gathering_Witness.objects.order_by('-creation_time')[:5]
  template = loader.get_template('action/index.html')
  context = {
    'latest_gathering_list': latest_gathering_list,
  }
  return HttpResponse(template.render(context, request))

def bad_link(request, error_message):
  template = loader.get_template('action/bad_link.html')
  context = { 'error_message': error_message }
  return HttpResponse(template.render(context, request))

def overview_by_name(request):
  loc_name = request.GET.get('location','')
  loc_exact = request.GET.get('exact','')
  loc_id = request.GET.get('locid','')
  return _overview_by_name(request, loc_name, loc_exact, loc_id)

def _overview_by_name(request, loc_name='', loc_exact='', loc_id=''):
  if not loc_name and not loc_id:
    return bad_link(request, "Something went wrong with this link (#11)")

  locations = []
  max_entries = 100
  sublocations = []
  sublocation_parent = None
  if loc_id:
    location_list = Location.objects.filter(id=int(loc_id))
    sublocation_parent = location_list.first()
  elif loc_exact:
    location_list = Location.objects.filter(name=loc_name)
    if len(location_list) == 1:
      sublocation_parent = location_list.first()
  else:
    if "," not in loc_name:
      # Simple search for a name
      location_list = Location.objects.filter(name__icontains=loc_name)
      if len(location_list) == 1:
        sublocation_parent = location_list.first()
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
          location_list += [cand_location]
      print(f"CLS9 location_list {location_list}")
  if sublocation_parent:
    sublocations = list(Location.objects.filter(in_location=sublocation_parent).order_by('name'))

  for loc in location_list[:max_entries]:
    gatherings = Gathering.objects.filter(location=loc)#.order_by('location.name')#'-start_date')
    print(f"OVX0 Gatherings {gatherings}")
    uniqe_gatherings = {}
    for gat in gatherings:
      print(f"OVX1 Gathering {gat}")
      cregid = gat.get_canonical_regid()
      if not cregid:
        print(f"OVBN Missing cregid {loc} {cregid} '{gat}'")
        continue
      gat = Gathering.objects.get(regid=cregid)
      print(f"OVX2 Gathering => {gat}")
      try:
        print(f"OVX3 Unique {cregid} {cregid not in uniqe_gatherings} {uniqe_gatherings}")
        if cregid not in uniqe_gatherings:
          print(f"OVX4 Unique {gat}")
          events = Gathering_Witness.objects.filter(gathering=cregid).count()
          participants = Gathering_Witness.objects.filter(gathering=cregid).aggregate(Sum('participants'))
          photos = Gathering_Witness.objects.filter(gathering=cregid).exclude(proof_url__exact='').count()
          uniqe_gatherings[cregid]=1
          print(f"OVX5 Unique {cregid} {cregid not in uniqe_gatherings} {uniqe_gatherings}")
          locations += [{
              'name':html.escape(loc.name), 
              'in_location': loc.in_location, 
              'gatherings': [{
                  'regid': gat.regid, 
                  'gathering_type': gat.get_gathering_type_str(), 
                  'start_date':gat.start_date,
                  'count': events,
                  'participants': participants.get('participants__sum'),
                  'photos': photos,
                }],
            }]
      except Exception as e:
        pass
        print(f"OVBN Exception looking up {loc} {cregid} '{gat}': {e}")

  if not sublocations and len(locations) == 1:
    print(f"OVBN shortcut {loc_name}")
    regid = locations[0]['gatherings'][0]['regid']
    return overview(request, regid, date=None, prev_participants=None, prev_url=None, error_message=None)
  elif sublocation_parent and sublocation_parent.in_location and not sublocations and not locations:
    # This is going to be a boring page, let's show the parent instead
    print(f"OVBP boring, switching to loc_id {sublocation_parent.in_location.id}")
    return _overview_by_name(request, loc_id=sublocation_parent.in_location.id)

  else:
    print(f"OVBN No shortcut: {len(sublocations)} {len(locations)} {sublocation_parent} {sublocation_parent.in_location if sublocation_parent else None}")

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
  #{% url 'action:overview' gat.regid %}
  return HttpResponse(template.render(context, request))

def overview(request, regid, date=None, prev_participants=None, prev_url=None, error_message=None):
  from django.template.defaulttags import register
  @register.filter
  def get_item(dictionary, key):
      return dictionary.get(key)

  regid = get_canonical_regid(regid)
  if not regid:
    return bad_link(request, "Something went wrong with this link (#21)")
  try:
    gathering_list = Gathering_Witness.objects.filter(gathering=regid).order_by('-date')
  except Gathering_Witness.DoesNotExist:
    gathering_list = []

  pin_colmap = {}
  pin_colors = set(['black'])
  for gathering in gathering_list:
    col = gathering.get_pin_color()
    pin_colmap[gathering.date] = col
    pin_colors.add(col)

  gat = Gathering.objects.get(regid=regid)
  print(f"ORG2 {gat.organizations.all()}")
  context = {
    'place_name': gat.get_place_name(),
    'in_location': gat.get_in_location(),
    'error_message': error_message,
    'date': date,
    'regid': regid,
    'gat': gat,
    'gat_organizations': [org.name for org in gat.organizations.all()],
    'gat_type': gat.get_gathering_type_str(),
    'gathering_list': gathering_list,
    'prev_participants': prev_participants,
    'prev_url': prev_url,
    'today': datetime.datetime.today(),
    'favorite_location': None,
    'colors': pin_colors,
    'colmap': pin_colmap,
  }

  if request.POST.get('favorite'):
    print(f"FAVV {request.POST.get('favorite')}")
    handle_favorite(request, regid)

  if request.user.is_authenticated:
    print(f"FAVU User {request.user.username}")
    try:
      userhome = UserHome.objects.get(callsign=request.user.username)
      gathering = Gathering.objects.get(regid=regid)
      context['favorite_location'] = str(gathering.location.id in [loc.id for loc in userhome.favorite_locations.all()])
      print(f"FAVQ {context['favorite_location']} {gathering.location.id} {userhome.favorite_locations.all()}")
    except:
      print(f"FAVF No userhome object for user {request.user.username}")
      userhome = None

  template = loader.get_template('action/report_results.html')
  return HttpResponse(template.render(context, request))

def handle_favorite(request, regid):
  print(f"FAVH {regid}")
  if request.user.is_authenticated:
    print(f"FAVX Authenticated")
    userhome = UserHome.objects.get(callsign=request.user.username)
    print(f"FAVU {request.user.username}")
    gathering = Gathering.objects.get(regid=regid)
    if userhome.favorite_locations.filter(id=gathering.location.id).count() == 0:
      print(f"FAVA {gathering.location.id}")
      userhome.favorite_locations.add(gathering.location.id)
    else:
      print(f"FAVR {gathering.location.id} {UserHome.objects.filter(favorite_locations__id=gathering.location.id)} {UserHome.favorite_locations.__dict__}")
      userhome.favorite_locations.remove(gathering.location.id)
    userhome.save()
    print(f"FAVS Saved {UserHome.favorite_locations} {UserHome.objects.filter(favorite_locations__id=gathering.location.id)}")

def report_results(request, regid):
  regid = get_canonical_regid(regid)
  if not regid:
    return bad_link(request, "Something went wrong with this link. (#31)")
  try:
    date = request.POST['date']
  except KeyError:
    # Redisplay the form
    return overview(request, regid, error_message="You must select a date for your results report.")
  return report_date(request, regid, date)

def report_date(request, regid, date):
  print(f"RDST report_date {regid} {date}")
  regid = get_canonical_regid(regid)
  if not regid:
    print("RDNO No regid")
    return bad_link(request, "Something went wrong with this link. (#33)")
  try:
    error_message = ""
    if request.POST.get('favorite'):
      pass
    else:
      participants = request.POST.get('participants')
      proof_url = request.POST.get('url')
      print(f"RDPP partricpants={participants} proof={proof_url}")

      gathering = Gathering.objects.filter(regid=regid).first()
      if gathering and participants != None and proof_url != None:
        try:
          Gathering_Witness.objects.filter(gathering=regid, date=date).delete()
          print(f"RDDL Deleted old Witness")
        except:
          pass
        witness = Gathering_Witness(
          gathering = gathering,
          date = date,
          participants = participants,
          proof_url = proof_url,
          updated = datetime.datetime.now())
        witness.save()
        error_message = f"Report for {date} Saved!"
        print(f"RDUP Updated witness {witness} {witness.__dict__}")

        organization_id = None
        try:
          organization_id = int(request.POST.get('organization'))
        except:
          pass
        print(f"RDOR Organization {organization_id}")
        if isinstance(organization_id, int):
          org = Organization.objects.filter(id = organization_id).first()
          if org:
            if org not in gathering.organizations.all():
              gathering.organizations.add(org)
              gathering.save()
              print(f"RDOA Organization {organization_id} added to {gathering.regid}")
            else:
              print(f"RDOD Organization {organization_id} already present in {gathering.regid}")
          else:
            print(f"RDOM Organization {organization_id} not found")
        else:
          print(f"RDOE Organization field empty or unchanged")
      else:
        print(f"RDNC No change")
  except Exception as e:
    print(f"RDXX Got Exception {e}")
    pass
  try:
    witness = Gathering_Witness.objects.get(gathering=regid, date=date)
    prev_participants = witness.participants
    prev_url = witness.proof_url
  except:
    print(f"RDNW No witness")
    prev_participants = 0
    prev_url = ""
  return overview(request, regid, 
    date=date, 
    prev_participants=prev_participants, 
    prev_url=prev_url, 
    error_message=error_message)

def upload_reg(request, error_message=None):
  context = {
    'error_message': error_message,
  }
  template = loader.get_template('action/upload_reg.html')
  return HttpResponse(template.render(context, request))

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
  print(f"UPSD Spooled {len(response_file_bytes)} bytes")
  return upload_reg(request, error_message=f"{len(response_file_bytes)} bytes successfully uploaded")

def download_upd(request, error_message=None):
  context = {
    'error_message': error_message,
  }
  template = loader.get_template('action/download_upd.html')
  return HttpResponse(template.render(context, request))

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
    t = datetime.datetime.fromisoformat(start_datetime+"+00:00")
    gupdates = Gathering_Witness.objects.filter(updated__gte=t)

    with io.StringIO(newline='') as csvfile:
      content = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
      for gupdate in gupdates:
        content.writerow(['Witness', 
          gupdate.gathering, gupdate.date, 
          gupdate.participants, gupdate.proof_url, 
          gupdate.creation_time, gupdate.updated])
      return HttpResponse(csvfile.getvalue(), content_type="text/plain")
  except Exception as e:
    print(f"DPXX Download exception: {e}")
    return download_upd(request, error_message="Download failed")

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
