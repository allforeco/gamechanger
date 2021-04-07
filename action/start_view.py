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
  raw_witness_list = list(Gathering_Witness.objects.filter(date__gte=datetime.datetime.today()-datetime.timedelta(days=22)))
  raw_witness_list.sort(key=lambda witness: witness.date if witness.date else datetime.datetime(1970,1,1), reverse=True)
  raw_witness_list = raw_witness_list[:20]

  template = loader.get_template('action/start.html')
  context = {
    'event_list': raw_witness_list,
  }

  return HttpResponse(template.render(context, request))