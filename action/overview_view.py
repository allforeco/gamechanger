from django.template import loader
from django.http import HttpResponse

from .models import Gathering_Witness, Location

import datetime

'''
??? latest 200 updated gathering_witness
'''
def latest_records_view(request):
  filter_amount = int(request.POST.get('filter_amount', '200'))
  record_list = list(Gathering_Witness.objects.order_by("-updated")[:filter_amount])
  witness_dict = {}
  print(f"LRV1 {len(record_list)}")
  for record in record_list:
    #print(f"LRV2 {record}")
    try:
      belong_regid = record.set_gathering_to_root()
      witness_dict[(belong_regid,record.date)] = record
    except:
      print(f"LRV4 Broken witness {record}")

  witness_list = list(witness_dict.values())
  witness_list.sort(key=lambda e: e.updated, reverse=True)
  print(f"LRV3 {len(witness_list)}")
  template = loader.get_template('action/latest_records_view.html')
  context = {
    'filter_amount': filter_amount,
    'record_list': witness_list,
  }

  return HttpResponse(template.render(context, request))

'''?UNUSED
___startpage list
'''
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

'''UNUSED
___view for user guide
'''
def help_view(request):

  print(f"PLVI |{Location.valid_ids(False)}|")

  template = loader.get_template('action/help_overview.html')
  context = {

  }

  return HttpResponse(template.render(context, request))