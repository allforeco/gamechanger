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
  filter_amount = int(request.POST.get('filter_amount', '200'))
  report_list = list(Gathering_Witness.objects.order_by("-updated")[:filter_amount])
  witness_dict = {}
  print(f"LRV1 {len(report_list)}")
  for report in report_list:
    #print(f"LRV2 {report}")
    try:
      belong_regid = report.set_gathering_to_root()
      witness_dict[(belong_regid,report.date)] = report
    except:
      print(f"LRV4 Broken witness {report}")

  witness_list = list(witness_dict.values())
  witness_list.sort(key=lambda e: e.updated, reverse=True)
  print(f"LRV3 {len(witness_list)}")
  template = loader.get_template('action/latest_reports_view.html')
  context = {
    'filter_amount': filter_amount,
    'report_list': witness_list,
  }

  return HttpResponse(template.render(context, request))

def locations_view(request):
  #print(f"LEND {len(list(Location.objects.all()))} | {len(Location.valid_ids())}")

  logginbypass = False
  location_list=list()
  template = loader.get_template('static/locations_overview.html')

  if request.user.is_authenticated or logginbypass:
    template = loader.get_template('action/locations_overview.html')
    location_list = Location.countries(false)
    location_list.sort(key=lambda e: e[0], reverse=False)
    for location in location_list:
      location[2].sort(key=lambda e: e[0], reverse=False)

  context = {
    'location_list': location_list,
    'logginbypass': logginbypass,
  }

  return HttpResponse(template.render(context, request))

def help_view(request):

  print(f"PLVI |{Location.valid_ids(False)}|")

  template = loader.get_template('action/help_overview.html')
  context = {

  }

  return HttpResponse(template.render(context, request))