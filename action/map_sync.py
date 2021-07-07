from django.template import loader
from django.http import HttpResponse
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from django import forms
from django.shortcuts import redirect
from .models import Gathering, Gathering_Belong, Gathering_Witness, Location, UserHome, Organization

import csv
import datetime as dateTime

def to_fff(self, dataset, title, params, debug=False):
  print(f"TOWM Web Map delivery of {len(dataset)} records")
  title += " generated on "+now_minute()
  payload = {"title":title, "csv": dataset.get_csv([title])}
  self._send_to_fff_web_server(payload)

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

def eventmap_data(request):
  with open('eventmap_data/eventmap_data.csv', 'w', newline='') as csvfile:
    datawriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    datawriter.writerow(['FFF Global Map generated on ' + dateTime.datetime.today().strftime('%Y-%m-%d %H:%M')]+['']*16)
    datawriter.writerow(
      ['Country']+
      ['Town']+
      ['Address']+
      ['Time']+
      ['Date']+
      ['End Date']+
      ["Link to event (URL), e.g. Facebook, Instagram, Twitter, web"]+
      ['Event Type']+
      ['Lat']+
      ['Lon']+
      ['Your name']+
      ['Email Address']+
      ['Phone number in international format (optional)']+
      ['Notes (optional)']+
      ['Organization that you represent (optional)']+
      ['Organizational Color']+
      ['gclink'])

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
              
              data_rows.update({eventmap_data.key: eventmap_data.data_row()})
              #if not eventmap_data.key in data_rows:
              #  data_rows.update({eventmap_data.key: eventmap_data.data_row()})
          else:
            data_rows.update({eventmap_data.key: eventmap_data.data_row()})
            #if not eventmap_data.key in data_rows:
            #  data_rows.update({eventmap_data.key: eventmap_data.data_row()})

    print(f"EDDR {data_rows}")
    datawriter.writerows(data_rows.values())
      
  
  return redirect('action:eventmap_data_view')

def eventmap_data_view(request):
  eventlist = []
  with open('eventmap_data/eventmap_data.csv', newline='') as csvfile:
    datareader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in datareader:
      eventlist.append(row)

  context = {
    'eventlist_lenght': (len(eventlist)-2),
    'eventlist': eventlist,
  }
  
  template = loader.get_template('action/eventmap_data.html')
  return HttpResponse(template.render(context, request))

class Eventmap_Data():
  object_location = None
  object_gathering = None
  object_witness = None

  country = ''
  town = ''
  address = ''
  time = ''
  date = ''
  frequency = '' #unused; frequency ?==> enddate
  date_end = ''
  proof_url = ''
  gathering_type = ''
  lat = ''
  lon = ''
  contact_name = ''
  contact_email = ''
  contact_phone = ''
  contact_notes = ''
  organization = ''
  organization_color = ''
  gc_link = '' #ok; regid ==> gc_link
  
  key = ''

  def data_process(self):
    
    #country, town, lat, lon, gc_link
    if self.object_location:
      temp = self.object_location
      for i in range(5):
        if temp.in_location:
          temp=temp.in_location
        else:
          self.country = temp.name
          break
      
      self.town = self.object_location.name
      self.lat = self.object_location.lat
      self.lon = self.object_location.lon
      self.gc_link = f"https://www.gamechanger.eco/action/geo/{self.object_location.id}/"
    
    #date, gathering_type, adress, time, contact_name, contact_email, contact_phone, contact_notes
    if self.object_gathering:
      self.date = self.object_gathering.start_date
      #self.frequency = self.object_gathering.frequency ==> end_date
      self.date_end = self.object_gathering.end_date
      self.gathering_type = self.object_gathering.get_gathering_type_str()
      self.address = self.object_gathering.address
      self.time = self.object_gathering.time
      self.organization = ", ".join(str(elem) for elem in list(self.object_gathering.organizations.all()))
      self.contact_name = self.object_gathering.contact_name
      self.contact_email = self.object_gathering.contact_email
      self.contact_phone = self.object_gathering.contact_phone
      self.contact_notes = self.object_gathering.contact_notes
      
    #date, proof_url, organization, organization_color
    if self.object_witness:
      self.date = self.object_witness.date
      self.date_end = self.object_witness.date
      self.proof_url = self.object_witness.proof_url
      self.organization = self.object_witness.organization
      self.organization_color = self.object_witness.get_pin_color()

    #self.key = self.object_gathering.regid
    self.key = f"{self.object_location.id}|{self.date}|{self.organization}"


  def data_row(self):
    self.data_process()
    return [self.country]+[self.town]+[self.address]+[self.time]+[self.date]+[self.date_end]+[self.proof_url]+[self.gathering_type]+[self.lat]+[self.lon]+[self.contact_name]+[self.contact_email]+[self.contact_phone]+[self.contact_notes]+[self.organization]+[self.organization_color]+[self.gc_link]