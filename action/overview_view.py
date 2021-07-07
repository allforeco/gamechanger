from django.template import loader
from django.http import HttpResponse
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from django import forms
from .models import Gathering, Gathering_Belong, Gathering_Witness, Location, UserHome, Organization
import datetime

def latest_reports_view(request):
  if (request.POST.get('filter_amount')):
    filter_amount = int(request.POST.get('filter_amount'))
  else:
    filter_amount = 200

  report_list = list(Gathering_Witness.objects.all())
  report_list.sort(key=lambda e: e.updated, reverse=True)
  report_list = report_list[:filter_amount]

  template = loader.get_template('action/latest_reports_view.html')
  context = {
    'filter_amount': filter_amount,
    'report_list': report_list,
  }

  return HttpResponse(template.render(context, request))

def locations_view(request):
  location_list = Location.objects.filter(lat__isnull=False)[:]
  location_dict=dict()

  for location in location_list:
    country = location
    for x in range(5):
      if country.in_location:
        country = country.in_location
      else:
        break
    
    if country.name in location_dict:
      location_dict[country.name][2].append([location.name, location.id])
    else:
      location_dict.update({country.name:[country.name, country.id, list()]})
      location_dict[country.name][2].append([location.name, location.id])

  location_list = list(location_dict.values())
  location_list.sort(key=lambda e: e[0], reverse=False)
  for location in location_list:
    location[2].sort(key=lambda e: e[0], reverse=False)

  template = loader.get_template('action/locations_overview.html')
  context = {
    'location_list': location_list,
  }

  return HttpResponse(template.render(context, request))