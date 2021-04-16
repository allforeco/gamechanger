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

def geo_view_handler(request, locid):
  print(f"TOWH {locid}")
  this_location = Location.objects.filter(id=locid).first()
  parent_location = this_location.in_location
  sublocation_list = Location.objects.filter(in_location=this_location)
  gathering_list = Gathering.objects.filter(location=this_location)
  witness_dict = {}
  print(f"TOWH {this_location} {parent_location} {len(sublocation_list)} {len(gathering_list)}")
  for gathering in gathering_list:
    raw_witness_list = list(Gathering_Witness.objects.filter(gathering=gathering))
    print(f"TOWI {gathering} {len(raw_witness_list)} {raw_witness_list}")
    for w in raw_witness_list:
      witness_dict[(w.gathering.regid,w.date)] = w
  witness_list = list(witness_dict.values())
  witness_list.sort(key=lambda e: e.date, reverse=True)
  total_participants = sum([w.participants for w in witness_list if w.participants])
  template = loader.get_template('action/geo_view.html')
  favorite_location = UserHome.objects.get(callsign=request.user.username).favorite_locations.filter(name=this_location.name).exists()
  context = {
    'this_location': this_location,
    'parent_location': parent_location,
    'sublocation_list': sublocation_list,
    'witness_list': witness_list,
    'total_participants': total_participants,
    'favorite_location': favorite_location,
  }

  if request.POST.get('favorite'):
    print(f"FAVV {request.POST.get('favorite')}")
    handle_favorite(request, this_location.id)

  if request.user.is_authenticated:
    print(f"FAVU User {request.user.username}")
    try:
      userhome = UserHome.objects.get(callsign=request.user.username)
      gathering = Gathering.objects.filter(location=locid).first()
      context['favorite_location'] = str(gathering.location.id in [loc.id for loc in userhome.favorite_locations.all()])
      print(f"FAVQ {context['favorite_location']} {gathering.location.id} {userhome.favorite_locations.all()}")
    except:
      print(f"FAVF No userhome object for user {request.user.username}")
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

class GeoUpdateView(UpdateView):
    model = Gathering_Witness
    fields = [ 'date', 'participants', 'proof_url' ] #, 'organization'
    template_name = 'action/geo_update_view.html'

    def get_success_url(self):
      print(f"TDDV success {self.__dict__}")    
      return reverse_lazy('action:geo_view', kwargs={'locid': self.object.gathering.location.id})
    def get_absolute_url(self):
      print(f"TDDV abs {self.__dict__}")    
      return reverse_lazy('geo_view', kwargs={'locid': self.gathering})


def handle_favorite(request, locid):
  print(f"FAVH {locid}")
  if request.user.is_authenticated:
    print(f"FAVX Authenticated")
    userhome = UserHome.objects.get(callsign=request.user.username)
    print(f"FAVU {request.user.username}")
    gathering = Gathering.objects.filter(location=locid).first()
    if userhome.favorite_locations.filter(id=gathering.location.id).count() == 0:
      print(f"FAVA {gathering.location.id}")
      userhome.favorite_locations.add(gathering.location.id)
    else:
      print(f"FAVR {gathering.location.id} {UserHome.objects.filter(favorite_locations__id=gathering.location.id)} {UserHome.favorite_locations.__dict__}")
      userhome.favorite_locations.remove(gathering.location.id)
    userhome.save()
    print(f"FAVS Saved {UserHome.favorite_locations} {UserHome.objects.filter(favorite_locations__id=gathering.location.id)}")

def translate_maplink(request, regid, date):
  print(f"RRRC {regid, date}")
  try:
    gathering_belong = Gathering_Belong.objects.filter(regid=regid).first()
    gathering = Gathering.objects.filter(regid=gathering_belong.gathering).first()
    locid = gathering.location.id
    print(f"RRRS '{regid}' --> '{locid}'")
    return redirect('action:geo_view', locid=locid)
  except:
    print(f"RRRF")
    return redirect('action:start')
