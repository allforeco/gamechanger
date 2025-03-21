from django.template import loader
from django.http import HttpResponse

from .models import Gathering, Gathering_Witness, Location, UserHome

import datetime

'''
===Handle startpage
'''

'''
___startpage view
___lists
'''
def start_view_handler(request):
  filter_weeks = datetime.timedelta(weeks=2) #int(request.POST.get('filter_weeks','2'))
  today = datetime.date.today()
  event_list = []

  gathering_list = Gathering.objects.filter(end_date__gte=today-filter_weeks).order_by("-start_date")

  #EVENT WITNESSING LOGIC
  event_record_head = Gathering.datalist_template(
    model=True, date=True, date_end=False, 
    location=True,event_link=True, gtype=True,
    recorded_link=True, map_link=True, 
    orgs=True, participants=True,
    coordinator=True, steward=True, guide=True,
    recorded=True,
    record=True, )
  gathering_witness_list = Gathering_Witness.objects.filter(date__range=[today-filter_weeks, today]).order_by("-date")
  for gw in gathering_witness_list:
    event_list.append(Gathering.datalist(gw, True, event_record_head, green=True if gw.participants else False))

  witnesses_here = Gathering_Witness.get_witnesses(gathering_list, event_record_head, already_listed=gathering_witness_list)
  event_list += [e for e in witnesses_here if e['date'] >= today-filter_weeks and e['date'] <= today]

  event_list.sort(key=lambda e: e['date'], reverse=True)

  template = loader.get_template('action/start.html')
  context = {
    'filter_weeks': filter_weeks.days // 7,
    'event_head': event_record_head,
    'event_list': event_list,
  }

  return HttpResponse(template.render(context, request))
