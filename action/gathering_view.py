from django.template import loader
from django.http import HttpResponse
from django.shortcuts import redirect
from django import forms

from .models import Gathering, Gathering_Witness, Gathering_Belong

'''
___organization view by id
'''
def gathering_view(request, regid):
  template = loader.get_template('action/gathering_overview.html')
  #print('regid', regid)
  gathering = Gathering.objects.get(regid=regid)
  event_main_head = Gathering.datalist_template(
    model=True, date=True, date_end=True, 
    gtype=False, note_address=True, note_time=True, 
    location=True, map_link=True, 
    orgs=True, recorded=True)
  event_main = [Gathering.datalist(gathering, False, event_main_head)]
  event_record_head = Gathering.datalist_template(
    model=True, date=True, 
    event_link=True, recorded_link=True, 
    location=False, participants=True,
    recorded=True)
  event_record_list = Gathering_Witness.get_witnesses(gathering, event_record_head)

  organization = None
  organization_view = None
  if gathering.organizations:
    organization = gathering.organizations.first()

  context = {
    'gathering': gathering,
    'event_main_head': event_main_head,
    'event_main': event_main,
    'event_record_head': event_record_head,
    'event_record_list': event_record_list,
    'organization':organization,
    'gathering_types':Gathering.gathering_type.field.choices,
    'logginbypass': True,
    }

  return HttpResponse(template.render(context, request))

