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

import datetime, io, csv, os, threading, html

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
from .models import Gathering, Gathering_Belong, Gathering_Witness, Location, UserHome
from django.contrib.auth.models import User

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
          }]
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
    print(f"AUTO Entered")
    if not self.request.user.is_authenticated:
      return Location.objects.none()
    qs = Location.objects.all()
    print(f"AUTO {len(qs)} locations")
    if self.q:
      qs = qs.filter(name__icontains=self.q)
    return qs

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

class GatheringSearch(FormView):
  template_name = 'action/gathering_search.html'
  form_class = GatheringSearchForm
  success_url = '/thanks/'

  def form_valid(self, form):
    return super().form_valid(form)

class GatheringCreate(CreateView):
  model = Gathering
  fields = ['gathering_type', 'location', 'start_date', 'end_date', 'duration', 'expected_participants']

  def get_success_url(self):
    return reverse_lazy('action:overview', kwargs={'regid': '11111111'})

  def form_valid(self, form):
    print(f"FORM valid")
    #form.send_email()
    return super().form_valid(form)

def spool_update_reg(response_file_bytes):
  print(f"INIT uwsgi req {len(response_file_bytes)}")
  action_spooler.spool(task=b'upload', body=response_file_bytes)
  print(f"INIT uwsgi spooled")

def get_place_name(regid):
  try:
    gatherings = Gathering.objects.filter(regid=regid)
    return gatherings.first().location.name
  except:
    return "Unknown Place"

def get_canonical_regid(regid):
  try:
    canonical_regid = Gathering_Belong.objects.filter(regid=regid).first().gathering.regid
    return canonical_regid
  except:
    return None

def index(request):
  latest_gathering_list = Gathering_Witness.objects.order_by('-creation_date')[:5]
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
  if not loc_name:
    return bad_link(request, "Something went wrong with this link (#11)")

  locations = []
  max_entries = 100
  location_list = Location.objects.filter(name__icontains=loc_name)
  for loc in location_list[:max_entries]:
    gatherings = Gathering.objects.filter(location=loc).order_by('-start_date')
    uniqe_gatherings = {}
    for gat in gatherings:
      cregid = gat.get_canonical_regid()
      if not cregid:
        print(f"OVBN Missing cregid {loc} {cregid} '{gat}'")
        break
      gat = Gathering.objects.get(regid=cregid)
      print(f"OVBN gat {loc} {cregid} '{gat}'")
      try:
        if cregid not in uniqe_gatherings:
          events = Gathering_Witness.objects.filter(gathering=cregid).count()
          participants = Gathering_Witness.objects.filter(gathering=cregid).aggregate(Sum('participants'))
          photos = Gathering_Witness.objects.filter(gathering=cregid).exclude(proof_url__exact='').count()
          uniqe_gatherings[cregid]=1
          locations += [{
              'name':html.escape(loc.name), 
              'gatherings': [{
                  'regid': gat.regid, 
                  'gathering_type': gat.get_gathering_type_str(), 
                  'start_date':gat.start_date,
                  'count': events,
                  'participants': participants.get('participants__sum'),
                  'photos': photos,
                } for gat in gatherings[:max_entries]],
            }]
      except Exception as e:
        pass
        print(f"OVBN Exception looking up {loc} {cregid} '{gat}': {e}")

  truncated = None
  if len(locations) == max_entries:
    truncated = f"... (search limited to {max_entries} results) ..."
  context = {
    'error_message': '',
    'locations': locations,
    'truncated': truncated
  }
  template = loader.get_template('action/location_overview.html')
  #{% url 'action:overview' gat.regid %}
  return HttpResponse(template.render(context, request))

def overview(request, regid, date=None, prev_participants=None, prev_url=None, error_message=None):
  regid = get_canonical_regid(regid)
  if not regid:
    return bad_link(request, "Something went wrong with this link (#21)")
  try:
    gathering_list = Gathering_Witness.objects.filter(gathering=regid).order_by('-date')
  except Gathering_Witness.DoesNotExist:
    gathering_list = []

  gat = Gathering.objects.get(regid=regid)
  context = {
    'place_name': get_place_name(regid),
    'error_message': error_message,
    'date': date,
    'regid': regid,
    'gat': gat,
    'gat_type': gat.get_gathering_type_str(),
    'gathering_list': gathering_list,
    'prev_participants': prev_participants,
    'prev_url': prev_url,
    'today': datetime.datetime.today(),
    'favorite_location': None,
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
  callsign = html.escape(raw_screenname).lower()
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
    loginuser = loginuser,
    visibility_level = visibility,
  )
  userhome.save()
  context = {'error_message': f"Callsign '{screenname}' successfully created."}
  return HttpResponse(template.render(context, request))
