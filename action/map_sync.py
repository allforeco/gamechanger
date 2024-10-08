from django.template import loader
from django.http import HttpResponse
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
#from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from django import forms
from django.shortcuts import redirect
from .models import Gathering, Gathering_Belong, Gathering_Witness, Location, UserHome, Organization
import io

import csv
import datetime as dateTime

'''
===read/write data coffer
'''

'''
???
'''
def to_fff(self, dataset, title, params, debug=False):
  print(f"TOWM Web Map delivery of {len(dataset)} records")
  title += " generated on "+now_minute()
  payload = {"title":title, "csv": dataset.get_csv([title])}
  self._send_to_fff_web_server(payload)

'''
???
'''
def _send_to_fff_web_server(self,payload,files=None):
  url = "https://map.fridaysforfuture.org/admin/inactive_upload/"
  cred = open(Env.get_or_die(Env.FFF_WEB_TOKEN_FILENAME), encoding="utf-8").read()
  payload["password"] = cred
  result = requests.post(url, data=payload, files=files)
  if(result.status_code == 200):
    print("UPFF Uploaded to fff.org.")
  else:
    print("NOFF Problem uploading to fff.org:\n%s"%result)
    raise (result.status_code, result.text)

'''
???read csv from ?coffer
'''
def coffer_data():
  with io.StringIO() as csvfile:
    datawriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    data_rows = dict()

    locations = list(Location.objects.filter(lat__isnull=False)[:]) #remove [:num] for full list
    for location in locations:
      eventmap_data = Eventmap_Data()
      eventmap_data.object_location = location

      gatherings = list(Gathering.objects.filter(location=location))
      gatherings.sort(key=lambda gathering: gathering.start_date if gathering.start_date else datetime.datetime(1970,1,1), reverse=True)
      if (len(gatherings) > 0):
        for gathering in gatherings:
          eventmap_data.object_gathering = gathering
          #data_rows.update({eventmap_data.key: eventmap_data.data_format_coffer()})

          witnesses = list(Gathering_Witness.objects.filter(gathering=gathering))
          witnesses.sort(key=lambda witness: witness.date if witness.date else datetime.datetime(1970,1,1), reverse=True)
          if (len(witnesses) > 0):
            for witness in witnesses:
              eventmap_data.object_witness = witness
              data_rows.update({eventmap_data.regid: eventmap_data.data_format_coffer()})
              #print(f"TESV {eventmap_data.data_format_coffer()} \n \n")

    #print(f"EDDR {data_rows}")
    datawriter.writerows(data_rows.values())
  
    #print(f"CSVO {csvfile}")
    return csvfile.getvalue()

'''
???write ? to csv
'''
def eventmap_data():
  with io.StringIO(newline='') as csvfile:
    datawriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    datawriter.writerow(['FFF Global Map generated on ' + dateTime.datetime.today().strftime('%Y-%m-%d %H:%M')]+['']*16)
    datawriter.writerow([
      'Country',
      'Town',
      'Address',
      'Time',
      'Date',
      'End Date',
      "Link to event (URL), e.g. Facebook, Instagram, Twitter, web",
      'Event Type',
      'Lat',
      'Lon',
      'Your name',
      'Email Address',
      'Phone number in international format (optional)',
      'Notes (optional)',
      'Organization that you represent (optional)',
      'Organizational Color',
      'regid'
    ])

    data_rows = dict()

    locations = list(Location.objects.filter(lat__isnull=False)[:]) #remove [:num] for full list
    for location in locations:
      eventmap_data = Eventmap_Data()
      eventmap_data.object_location = location

      gatherings = list(Gathering.objects.filter(location=location))
      gatherings.sort(key=lambda gathering: gathering.start_date if gathering.start_date else datetime.datetime(1970,1,1), reverse=True)
      if (len(gatherings) > 0):
        for gathering in gatherings:
          eventmap_data.object_gathering = gathering

          witnesses = list(Gathering_Witness.objects.filter(gathering=gathering))
          witnesses.sort(key=lambda witness: witness.date if witness.date else datetime.datetime(1970,1,1), reverse=True)
          if (len(witnesses) > 0):
            for witness in witnesses:
              eventmap_data.object_witness = witness
              
              data_rows.update({eventmap_data.regid: eventmap_data.data_format_map()})
          else:
            data_rows.update({eventmap_data.regid: eventmap_data.data_format_map()()})

    print(f"EDDR {data_rows}")
    datawriter.writerows(data_rows.values())
      
  return csvfile

'''
???view for reading event_map_data csv data
'''
def eventmap_data_view(request):
  eventlist = []
  datareader = csv.reader(open(eventmap_data(), newline=''), delimiter=',', quotechar='"')
  for row in datareader:
    eventlist.append(row)

  context = {
    'eventlist_length': (len(eventlist)-2),
    'eventlist': eventlist,
  }
  
  template = loader.get_template('action/eventmap_data.html')
  return HttpResponse(template.render(context, request))

'''
???class for parsing event_map_data csv
'''
class Eventmap_Data():
  object_location = None
  object_gathering = None
  object_witness = None

  source = 'Gamechanger' #C

  #LOCATION
  country = '' #CM
  town = '' #CM
  lat = '' #CM
  lon = '' #CM
  location_google_name = '' #C

  #GATHERING; WITNESS
  create_time = '' #C
  update_time = '' #C
  organization = '' #CM
  participants = '' #CM
  date = '' #CM

  #GATHERING
  #create_time = '' #C
  #update_time = '' #C
  regid = '' #CM
  gathering_type = '' #CM
  #participants = '' #CM
  #organization = '' #CM
  organization_color = '' #M
  #date = '' #CM
  date_end = '' #M
  frequency = 'once' #C : 'once', 'weekly', 'every friday'
  time = '' #CM
  address = '' #CM
  contact_approval = 'y' #C
  contact_accsess_level = '' #Private, Press, Public
  contact_name = '' # CM
  contact_email = '' # CM
  contact_phone = ''  #M
  contact_notes = '' #M
  
  #WITNESS
  #create_time = '' #C
  #update_time = '' #C
  #date = '' #CM
  #participants = '' #CM
  #organization = '' #CM
  proof_url = '' #CM

  def data_process_location(self):
    #LOCATION; country, town, lat, lon, location_google_name
    if self.object_location:
      self.country = self.object_location.country_location()
      self.town = self.object_location.name
      self.lat = self.object_location.lat
      self.lon = self.object_location.lon
      #self.location_google_name = self.object_location.google_name

  def data_process_gathering(self):
    #GATHERING; create_time, update_time, 
    # regid, gathering_type, participants, organization, ?organization_color?, date, date_end, frequency, time, adress, 
    # contact_approval, contact_name, contact_email, contact_phone, contact_notes
    if self.object_gathering:
      #self.create_time = self.object_gathering.creation_time
      #self.update_time = self.object_gathering.updated

      self.regid = self.object_gathering.regid

      self.date = self.object_gathering.start_date
      self.date_end = self.object_gathering.end_date
      if (self.date != self.date_end):
        self.frequency = 'weekly'

      self.gathering_type = self.object_gathering.get_gathering_type_str()
      if self.object_gathering.expected_participants:
        self.participants = self.object_gathering.expected_participants
      if self.object_gathering.address:
        self.address = self.object_gathering.address
      if self.object_gathering.time:
        self.time = self.object_gathering.time
      if len(self.object_gathering.organizations.all()) > 0:
        self.organization = ", ".join(str(elem) for elem in list(self.object_gathering.organizations.all()))
      
      if (self.contact_approval == 'y'):
        if self.object_gathering.contact_name:
          self.contact_name = self.object_gathering.contact_name
        if self.object_gathering.contact_email:
          self.contact_email = self.object_gathering.contact_email
        if self.object_gathering.contact_phone:
          self.contact_phone = self.object_gathering.contact_phone
        if self.object_gathering.contact_notes:
          self.contact_notes = self.object_gathering.contact_notes
      else:
        self.contact_name = self.object_gathering.contact_name = 'anonymus'
        self.contact_email = self.object_gathering.contact_email = 'map@fff'
        self.contact_notes = self.object_gathering.contact_notes = 'Anonymus registration'

  def data_process_witness(self):
    #WITNESS; 
    # >create_time<, >update_time<, 
    # >date<, *date_end*, *frequency*, participants, >organization<, organization_color
    if self.object_witness:
      self.create_time = self.object_witness.creation_time
      self.update_time = self.object_witness.updated

      self.date = self.object_witness.date
      self.date_end = self.object_witness.date
      #DEFAULT: self.frequency = 'Once'

      if self.object_witness.participants:
        self.participants = self.object_witness.participants

      if self.object_witness.proof_url:
        self.proof_url = self.object_witness.proof_url
      if self.object_witness.organization:
        self.organization = self.object_witness.organization
      else:
        self.organization = ''
      self.organization_color = self.object_witness.get_pin_color()

  def data_process_all(self):
    self.data_process_location()
    self.data_process_gathering()
    self.data_process_witness()
      
  def data_format_map(self):
    self.data_process_all()
    return [
      self.country,
      self.town,
      self.address,
      self.time,
      self.date,
      self.date_end,
      self.proof_url,
      self.gathering_type,
      self.lat,
      self.lon,
      self.contact_name,
      self.contact_email,
      self.contact_phone,
      self.contact_notes,
      self.organization,
      self.organization_color,
      self.regid,
    ]

  def data_format_coffer(self):
    self.data_process_all()
    return [
      'Witness',
      self.regid,
      self.date,
      self.participants,
      self.proof_url,
      self.create_time,
      self.update_time,
      self.organization,
    ]
