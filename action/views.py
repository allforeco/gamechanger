import datetime, io, csv, os

from django.shortcuts import render
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

from django.http import HttpResponse
from .models import Gathering, Gathering_Belong, Gathering_Witness
from . import update_reg

def get_place_name(regid):
  try:
    gatherings = Gathering.objects.filter(regid=regid)
    return gatherings.first().location.name
  except:
    return "Unknown Place"

def get_canonical_regid(regid):
  canonical_regid = Gathering_Belong.objects.filter(regid=regid).first().gathering.regid
  return canonical_regid

def index(request):
  latest_gathering_list = Gathering_Witness.objects.order_by('-creation_date')[:5]
  template = loader.get_template('action/index.html')
  context = {
    'latest_gathering_list': latest_gathering_list,
  }
  return HttpResponse(template.render(context, request))

def overview(request, regid, date=None, prev_participants=None, prev_url=None, error_message=None):
  regid = get_canonical_regid(regid)
  try:
    gathering_list = Gathering_Witness.objects.filter(gathering=regid).order_by('-date')
  except Gathering_Witness.DoesNotExist:
    gathering_list = []

  context = {
    'place_name': get_place_name(regid),
    'error_message': error_message,
    'date': date,
    'regid': regid,
    'gathering_list': gathering_list,
    'prev_participants': prev_participants,
    'prev_url': prev_url,
    'today': datetime.datetime.today(),
  }
  template = loader.get_template('action/report_results.html')
  return HttpResponse(template.render(context, request))

def report_results(request, regid):
  regid = get_canonical_regid(regid)
  try:
    date = request.POST['date']
  except KeyError:
    # Redisplay the form
    return overview(request, regid, error_message="You must select a date for your results report.")
  return report_date(request, regid, date)

def report_date(request, regid, date):
  regid = get_canonical_regid(regid)
  error_message = ""
  try:
    participants = request.POST['participants']
    proof_url = request.POST['url']

    gathering = Gathering.objects.filter(regid=regid).first()
    try:
      Gathering_Witness.objects.filter(gathering=regid, date=date).delete()
    except:
      pass
    witness = Gathering_Witness(
      gathering = gathering,
      date = date,
      participants = participants,
      proof_url = proof_url,
      updated = datetime.datetime.now())
    witness.save()
    error_message = f"Report for {date} Saved!"
  except Exception as e:
    # Initially
    pass
  try:
    witness = Gathering_Witness.objects.get(gathering=regid, date=date)
    prev_participants = witness.participants
    prev_url = witness.proof_url
  except:
    prev_participants = 0
    prev_url = ""
  return overview(request, regid, 
    date=date, 
    prev_participants=prev_participants, 
    prev_url=prev_url, 
    error_message=error_message)

def upload_reg(request, error_message=None):
  context = {
    'error_message': error_message,
  }
  template = loader.get_template('action/upload_reg.html')
  return HttpResponse(template.render(context, request))

def upload_post(request):
  try:
    token = request.POST['token']
    regfile = request.FILES['regfile']
  except KeyError:
    # Redisplay the form
    print(20)
    return upload_reg(request, error_message="You must specify a RegID file")

  if token != os.environ['GAMECHANGER_UPLOAD_TOKEN']:
    return upload_reg(request, error_message="You must specify a valid RegID file")

  response_file = io.StringIO(regfile.read().decode('utf-8'))
  response_reader = csv.reader(response_file, delimiter=',')
  response_list = list(response_reader)
  count = update_reg.update_reg(response_list)
  count_of = len(response_list)
  return upload_reg(request, error_message=f"{count}/{count_of} place definitions successfully uploaded")

def download_upd(request, error_message=None):
  context = {
    'error_message': error_message,
  }
  template = loader.get_template('action/download_upd.html')
  return HttpResponse(template.render(context, request))

@csrf_exempt
def download_post(request):
  try:
    token = request.POST['token']
    start_datetime = request.POST['start_datetime']
  except KeyError:
    # Redisplay the form
    return download_upd(request, error_message="You must specify a start date and time")

  if token != os.environ['GAMECHANGER_UPLOAD_TOKEN']:
    return download_upd(request, error_message="You must specify a valid start date and time")

  try:
    t = datetime.datetime.fromisoformat(start_datetime+"+00:00")
    gupdates = Gathering_Witness.objects.filter(updated__gte=t)

    with io.StringIO(newline='') as csvfile:
      content = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
      for gupdate in gupdates:
        content.writerow(['Witness', 
          gupdate.gathering, gupdate.date, 
          gupdate.participants, gupdate.proof_url, 
          gupdate.creation_time, gupdate.updated])
      return HttpResponse(csvfile.getvalue(), content_type="text/plain")
  except Exception as e:
    print(f"Download exception: {e}")
    return download_upd(request, error_message="Download failed")
