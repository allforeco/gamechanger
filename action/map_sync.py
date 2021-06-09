from django.template import loader
from django.http import HttpResponse
from django.views.generic.edit import FormView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required, permission_required
from django import forms
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
  csvdisplay = []
  with open('eventmap_data.csv', 'w', newline='') as csvfile:
    datawriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    datawriter.writerow(['FFF Global Map generated on ' + dateTime.datetime.today().strftime('%Y-%m-%d %H:%M')]+['']*16)
    datawriter.writerow(
      ['Country']+
      ['Town']+
      ['Address']+
      ['Time']+
      ['Date']+
      ['Frequency']+
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

    locations = list(Location.objects.filter(lat__isnull=False)[:333])
    for location in locations:
      d_country = ''
      d_town = ''
      d_adress = ''
      d_time = ''
      d_date = ''
      d_frequency = ''
      d_witness_event_link = ''
      d_gathering_type = ''
      d_lat = ''
      d_lon = ''
      d_witness_name = ''
      d_witness_email = ''
      d_witness_phone = ''
      d_notes = ''
      d_organization = ''
      d_organization_color = ''
      d_gc_link = ''

      country = location
      for i in range(4):
        if (country.in_location):
          country = country.in_location
        else:
          d_country = country

      d_town = location
      d_lat = location.lat
      d_lon = location.lon
      d_gc_link = ('https://www.gamechanger.eco/action/geo/' +str(location.id)+'/').split('/')[-2]

      gatherings = list(Gathering.objects.filter(location=location))
      gatherings.sort(key=lambda gathering: gathering.start_date if gathering.start_date else datetime.datetime(1970,1,1), reverse=True)
      
      if (len(gatherings) > 0):
        for gathering in gatherings:
          d_date = gathering.start_date
          d_gathering_type = gathering.get_gathering_type_str()
          #d_organization = gathering.organizations
          #d_adress = gathering.address
          #d_time = gathering.time

          witnesses = list(Gathering_Witness.objects.filter(gathering=gathering))
          witnesses.sort(key=lambda witness: witness.date if witness.date else datetime.datetime(1970,1,1), reverse=True)
          
          if (len(witnesses) > 0):
            for witness in witnesses:
              d_date = witness.date
              if (len(witness.proof_url.split('/')) > 1):
                d_witness_event_link = witness.proof_url.split('/')[2]
              d_organization = witness.organization
              d_organization_color = witness.get_pin_color()

              datawriter.writerow(
                [d_country]+
                [d_town]+
                [d_adress]+
                [d_time]+
                [d_date]+
                [d_frequency]+
                [d_witness_event_link]+
                [d_gathering_type]+
                [d_lat]+
                [d_lon]+
                [d_witness_name]+
                [d_witness_email]+
                [d_witness_phone]+
                [d_notes]+
                [d_organization]+
                [d_organization_color]+
                [d_gc_link])
          else:
            datawriter.writerow(
                [d_country]+
                [d_town]+
                [d_adress]+
                [d_time]+
                [d_date]+
                [d_frequency]+
                [d_witness_event_link]+
                [d_gathering_type]+
                [d_lat]+
                [d_lon]+
                [d_witness_name]+
                [d_witness_email]+
                [d_witness_phone]+
                [d_notes]+
                [d_organization]+
                [d_organization_color]+
                [d_gc_link])
      else:
        datawriter.writerow(
          [d_country]+
          [d_town]+
          [d_adress]+
          [d_time]+
          [d_date]+
          [d_frequency]+
          [d_witness_event_link]+
          [d_gathering_type]+
          [d_lat]+
          [d_lon]+
          [d_witness_name]+
          [d_witness_email]+
          [d_witness_phone]+
          [d_notes]+
          [d_organization]+
          [d_organization_color]+
          [d_gc_link])

    


  with open('eventmap_data.csv', newline='') as csvfile:
    datareader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in datareader:
      csvdisplay.append(row)

  context = {
    'csvfile': csvdisplay,
  }
  return HttpResponse(loader.get_template('action/eventmap_data.html').render(context, request))