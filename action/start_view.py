from django.template import loader
from django.http import HttpResponse
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from django import forms
from .models import Gathering, Gathering_Belong, Gathering_Witness, Location, UserHome, Organization
import datetime

def start_view_handler(request):
  filter_weeks = int(request.POST.get('filter_weeks','2'))
  list_length = 50

  #GATHERING PLAN LOGIC
  gathering_list = list(Gathering.objects.filter(start_date__gte=(datetime.datetime.today()-datetime.timedelta(days=1)))[:list_length])
  gathering_dict = {}
  for g in gathering_list:
    belong_regid = g.get_gathering_root()
    gathering_dict[(belong_regid,g.start_date)] = g
  gathering_list = list(gathering_dict.values())
  gathering_list.sort(key=lambda e: e.start_date, reverse=False)
  gatherings = list()
  for gathering in gathering_list:
    try:
      gathering_data = list()
      gathering_data.append(gathering.start_date.strftime('%Y-%m-%d'))
      gathering_data.append(gathering.get_gathering_type_str())
      gathering_data.append(gathering.get_gathering_root())
      gathering_data.append([gathering.location.id, gathering.location.name])
      gathering_data.append(gathering.organizations.first())
      gathering_data.append(gathering.expected_participants)

      gatherings.append(gathering_data)
    except:
      print(f"SVX0 Cannot display broken {gathering}")
  
  #EVENT WITNESSING LOGIC
  report_list = list(Gathering_Witness.objects.filter(updated__gte=datetime.datetime.today()-datetime.timedelta(days=7*filter_weeks))[:list_length])
  witness_dict = {}
  for w in report_list:
    belong_regid = w.set_gathering_to_root()
    witness_dict[(belong_regid,w.date)] = w
  witness_list = list(witness_dict.values())
  witness_list.sort(key=lambda e: e.updated, reverse=True)

  reports = list()
  i = 0
  for report in witness_list:
    report_data = list()
    i+=1
    report_data.append(i)
    report_data.append(report.date.strftime('%Y-%m-%d'))
    if report.gathering:
      report_data.append(report.gathering.regid)
      report_data.append([report.gathering.location.id, report.gathering.location.name])
      report_data.append(report.organization)
      report_data.append(report.participants)
      report_data.append(report.proof_url)

      reports.append(report_data)
  
  #LEADERBOARD LOGIC
  leaderboard_dict=dict()

  for gathering in gathering_list:
    if (gathering.location):
      location = gathering.location
      for x in range(5):
        if location.in_location:
          location = location.in_location
        else:
          break
    else:
      location = Location.objects.filter(name='Unknown Place').first()

    if location.name in leaderboard_dict:
      leaderboard_dict[location.name][2] += 1
    else:
      leaderboard_dict.update({location.name: [location.name, location.id, 1, 0]})

  for witness in report_list:
    if (witness.gathering):
      location = witness.gathering.location
      for x in range(5):
        if location.in_location:
          location = location.in_location
        else:
          break
    else:
      location = Location.objects.filter(name='Unknown Place').first()

    if location.name in leaderboard_dict:
      leaderboard_dict[location.name][3] += 1
    else:
      leaderboard_dict.update({location.name: [location.name, location.id, 0, 1]})
  
  leaderboard = list(leaderboard_dict.values()) 
  leaderboard.sort(key=lambda e: e[2], reverse=True)
  leaderboard = leaderboard[:list_length]

  template = loader.get_template('action/start.html')
  context = {
    'filter_weeks': filter_weeks,
    'report_list': reports,
    'gathering_list': gatherings,
    'leaderboard_list': leaderboard,
  }

  return HttpResponse(template.render(context, request))