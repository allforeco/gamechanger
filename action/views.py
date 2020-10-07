import datetime

from django.shortcuts import render
from django.template import loader

# Create your views here.

from django.http import HttpResponse
from .models import Gathering, Gathering_Witness

def get_place_name(reg_id):
  place_map = {
    '11111111': 'Stockholm'
  }
  return place_map.get(reg_id, "Unknown Place")

def index(request):
  latest_gathering_list = Gathering_Witness.objects.order_by('-creation_date')[:5]
  template = loader.get_template('action/index.html')
  context = {
    'latest_gathering_list': latest_gathering_list,
  }
  return HttpResponse(template.render(context, request))

def overview(request, reg_id, date=None, prev_participants=None, prev_url=None, error_message=None):
  try:
    gathering_list = Gathering_Witness.objects.filter(gathering=reg_id).order_by('-date')
  except Gathering_Witness.DoesNotExist:
    gathering_list = []

  context = {
    'place_name': get_place_name(reg_id),
    'error_message': error_message,
    'date': date,
    'reg_id': reg_id,
    'gathering_list': gathering_list,
    'prev_participants': prev_participants,
    'prev_url': prev_url,
    'today': datetime.datetime.today(),
  }
  template = loader.get_template('action/report_results.html')
  return HttpResponse(template.render(context, request))

def report_results(request, reg_id):
  try:
    date = request.POST['date']
  except KeyError:
    # Redisplay the form
    return overview(request, reg_id, error_message="You must select a date for your results report.")
  return report_date(request, reg_id, date)

def report_date(request, reg_id, date):
  error_message = ""
  try:
    participants = request.POST['participants']
    proof_url = request.POST['url']

    gathering = Gathering(regid=reg_id, 
      start_date_time=datetime.datetime.today(),
      end_date_time=datetime.datetime.today())
    gathering.save()
    try:
      Gathering_Witness.objects.filter(gathering=reg_id, date=date).delete()
    except:
      pass
    witness = Gathering_Witness(
      gathering = gathering,
      date = date,
      participants = participants,
      proof_url = proof_url)
    witness.save()
    error_message = f"Report for {date} Saved!"
  except Exception as e:
    # Initially
    pass
  try:
    witness = Gathering_Witness.objects.get(gathering=reg_id, date=date)
    prev_participants = witness.participants
    prev_url = witness.proof_url
  except:
    prev_participants = 0
    prev_url = ""
  return overview(request, reg_id, 
    date=date, 
    prev_participants=prev_participants, 
    prev_url=prev_url, 
    error_message=error_message)
