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
  print('regid', regid)
  gathering = Gathering.objects.get(regid=regid)
  gathering_witness_list = Gathering_Witness.objects.filter(gathering=gathering).order_by('-date')[:100]
  organization = None
  organization_view = None
  if gathering.organizations:
    organization = gathering.organizations.first()

  context = {
    'gathering':gathering,
    'gathering_witness_list':gathering_witness_list,
    'organization':organization,
    }

  return HttpResponse(template.render(context, request))

