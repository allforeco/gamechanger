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
  filter_weeks = datetime.timedelta(weeks=4) #int(request.POST.get('filter_weeks','2'))
  list_length = 50
  today = datetime.datetime.today()

  #LEADERBOARD LOGIC
  leaderboard_dict=dict()
  def leaderboard_append(country, isrecord):
    index = 1
    if isrecord:
      index = 2
    if not country in leaderboard_dict:
      leaderboard_dict[country]=[0,0,0]
    leaderboard_dict[country][0]+=1
    leaderboard_dict[country][index]+=1

  #GATHERING PLAN LOGIC
  event_plan_head = Gathering.datalist_template(
    model=True, date=True, date_end=True, 
    location=True, map_link=True, 
    orgs=True, participants=True,
    recorded=True, overview=True,
    steward=True)
  gathering_plans = Gathering.objects.filter(end_date__range=[today, today+filter_weeks]).order_by("-start_date")
  event_plan_list = []

  for gp in gathering_plans:
    event_plan_list.append(Gathering.datalist(gp, False, event_plan_head))
    leaderboard_append(gp.location.country_location(), False)

  #EVENT WITNESSING LOGIC
  event_record_head = Gathering.datalist_template(
    model=True, date=True, date_end=False, 
    location=True,event_link=True,
    recorded_link=True, map_link=True, 
    orgs=True, participants=True,
    recorded=True, overview=True,
    steward=True)
  gathering_witness = Gathering_Witness.objects.filter(updated__range=[today-filter_weeks, today]).order_by("-date")
  gathering_witness_list = []
  for gw in gathering_witness:
    gathering_witness_list.append(Gathering.datalist(gw, True, event_record_head))
    leaderboard_append(gw.gathering.location.country_location(), True)

  leaderboard = []
  for item in leaderboard_dict.items():
    leaderboard.append([item[0],item[1][0],item[1][1],item[1][2]])
  leaderboard.sort(key=lambda e: e[1], reverse=True)
  #leaderboard = leaderboard_dict.items()
  print(leaderboard)
  #sorted(leaderboard, key=lambda e: (leaderboard_dict[e][0]), reverse=True)

  template = loader.get_template('action/start.html')
  context = {
    'filter_weeks': filter_weeks,
    'event_plan_head': event_plan_head,
    'event_record_head': event_record_head,
    'plan_list': event_plan_list,
    'witness_list': gathering_witness_list,
    'leaderboard_list': leaderboard,
  }

  return HttpResponse(template.render(context, request))

  #for g in gathering_list:
    #belong_regid = g.get_gathering_root()
    #gathering_dict[(belong_regid,g.start_date)] = g
  #gathering_list = list(gathering_dict.values())
  #gathering_list.sort(key=lambda e: e.start_date, reverse=False)
  #gatherings = list()
  #for gathering in gathering_list:
    #try:
      #gathering_data = list()
      #gathering_data.append(gathering.start_date.strftime('%Y-%m-%d'))
      #gathering_data.append(gathering.get_gathering_type_str())
      #gathering_data.append(gathering.get_gathering_root())
      #gathering_data.append([gathering.location.id, gathering.location.name])
      #gathering_data.append(gathering.organizations.first())
      #gathering_data.append(gathering.expected_participants)
#
      #gatherings.append(gathering_data)
    #except:
      #print(f"SVX0 Cannot display broken {gathering}")
  
  #EVENT WITNESSING LOGIC
  #...
  #record_list = list(Gathering_Witness.objects.order_by("-updated").filter(updated__gte=datetime.datetime.today()-datetime.timedelta(days=7*filter_weeks))[:list_length])
  #witness_dict = {}
  #for w in record_list:
    #belong_regid = w.set_gathering_to_root()
    #witness_dict[(belong_regid,w.date)] = w
  #witness_list = list(witness_dict.values())
  #witness_list.sort(key=lambda e: e.updated, reverse=True)
#
  #records = list()
  #i = 0
  #for record in witness_list:
    #record_data = list()
    #i+=1
    #record_data.append(i)
    #record_data.append(record.date.strftime('%Y-%m-%d'))
    #if record.gathering:
      #record_data.append(record.gathering.regid)
      #record_data.append([record.gathering.location.id, record.gathering.location.name])
      #record_data.append(record.organization)
      #record_data.append(record.participants)
      #record_data.append(record.proof_url)
#
      #records.append(record_data)
  
  #LEADERBOARD LOGIC
  #leaderboard_dict=dict()
#
  #for gathering in gathering_list:
    #if (gathering.location):
      #location = gathering.location
      #for x in range(5):
        #if location.in_location:
          #location = location.in_location
        #else:
          #break
    #else:
      #location = Location.objects.filter(name='Unknown Place').first()
#
    #if location.name in leaderboard_dict:
      #leaderboard_dict[location.name][2] += 1
    #else:
      #leaderboard_dict.update({location.name: [location.name, location.id, 1, 0]})
#
  #for witness in record_list:
    #if (witness.gathering):
      #location = witness.gathering.location
      #for x in range(5):
        #if location.in_location:
          #location = location.in_location
        #else:
          #break
    #else:
      #location = Location.objects.filter(name='Unknown Place').first()
#
    #if location.name in leaderboard_dict:
      #leaderboard_dict[location.name][3] += 1
    #else:
      #leaderboard_dict.update({location.name: [location.name, location.id, 0, 1]})
#  
  #leaderboard = list(leaderboard_dict.values()) 
  #leaderboard.sort(key=lambda e: e[2], reverse=True)
  #leaderboard = leaderboard[:list_length]

  template = loader.get_template('action/start.html')
  context = {
    'filter_weeks': filter_weeks,
    'event_head': event_head,
    'plan_list': event_plan_list,
    'witness_list': gathering_witness_list,
    'leaderboard_list': leaderboard,
  }

  return HttpResponse(template.render(context, request))