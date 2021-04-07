from django.template import loader
from django.http import HttpResponse
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from django import forms
from .models import Gathering, Gathering_Belong, Gathering_Witness, Location, UserHome, Organization
import datetime

def top_reporters_view_handler(request):
  countries_report_dict=dict()

  raw_witness_list = list(Gathering_Witness.objects.filter(date__gte=datetime.datetime.today()-datetime.timedelta(days=30)))
  for witness in raw_witness_list:
    location = witness.gathering.location
    for x in range(0,8):
      if location.in_location:
        location = location.in_location
      else:
        break
    
    countries_report_dict[location] = countries_report_dict.get(location, 0)+1

  countries_report_list = [(location.name, countries_report_dict[location], location.id) for location in countries_report_dict] 
  
  countries_report_list.sort(key=lambda e: e[1], reverse=True)

  template = loader.get_template('action/top_reporters.html')
  context = {
    'reports_list': countries_report_list,
  }

  return HttpResponse(template.render(context, request))
