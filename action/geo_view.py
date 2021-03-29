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
  context = {
    'this_location': this_location,
    'parent_location': parent_location,
    'sublocation_list': sublocation_list,
    'witness_list': witness_list,
    'total_participants': total_participants,
  }
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

