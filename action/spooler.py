#   Gamechanger Action Spooler
#   Copyright (C) 2020 Jan Lindblad
# 
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
# 
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime, io, csv
from uwsgidecorators import spool
from .models import Location, Gathering, Gathering_Belong, Gathering_Witness

try:
  import uwsgi
  print(f"INIT uWSGI imported in spooler")
except ImportError:
  uwsgi = None
  print(f"INIT uWSGI not found in spooler")

@spool
def action_spooler(req):
  task = req.get('task')
  print(f"SPOL Gamechanger spooler running, got {task} job")
  body = req.get('body')
  if body:
    print(f"SSMP Body len {len(body)} sample '{str(body)[:100]}'...")
  if task == 'upload' and body:
    task_update_reg(body)
  else:
    print('SUNK Unknown spool job type')
  print(f"SEND Gamechanger spooler job complete")
  return uwsgi.SPOOL_OK

def task_update_reg(body):
  reg_file = io.StringIO(body)
  reg_reader = csv.reader(reg_file, delimiter=',')
  doctype_line = reg_reader.__next__()
  doctype = doctype_line[0]
  if not doctype.startswith('FFF RegID'):
    print(f"URDT Bad doctype '{doctype}'")
    return uwsgi.SPOOL_OK

  reg_list = [line for line in reg_reader]
  count_of = len(reg_list)
  print(f"URLN {count_of} place definitions to process")
  update_reg(reg_list)
  print(f"URES place definitions processed")

def get_update_timestamp(timestr):
  if timestr:
    try:
      return datetime.datetime.strptime(timestr, "%Y-%m-%dT%H:%M:%S")
    except:
      pass
  long_ago = datetime.datetime(1970, 1, 1, 0, 0, 0, 0)
  return long_ago

def update_reg(regs):
  print("UREG Updating regid registry")

  headers = regs[0] # RID,RUPD,GLOC,EDATE,EENDDATE,REVNUM,REVPROOF
  print(f"URHD Read headers {headers}")
  line_count = len(regs)
  counter = {'Completed':0, 'Location':0, 'Gathering':0, 'Gathering_Belong':0, 
             'Gathering_Witness':0, 'Witness Updated':0, 'Witness Not Updated':0}
  for lineno, line in enumerate(regs[1:], 1):
    if lineno % 1000 == 1:
      print(f"URCT {lineno-1} {counter}")

    rec = {}
    for col, val in enumerate(line):
      rec[headers[col]] = val
    regid = rec.get('RID', None)
    edate = rec.get('EDATE', None)
    if not regid or not edate:
      print(f"URBR Skipping record {lineno} {regid} {edate}")
      continue

    try:
      max_length = Location._meta.get_field('name').max_length
      loc_name = rec.get('GLOC','')[:max_length]
      if not loc_name:
        location = Location.objects.filter(name = 'Unknown Place')
        if not location:
          location = Location(name = 'Unknown Place')
          location.save()
        print(f"URUL {lineno} {regid} Unknown location")
      else:
        location = Location.objects.filter(name = loc_name).first()
        if not location:
          location = Location(name = loc_name)
          #print(f"Adding location {location}")
          location.save()
          counter['Location'] += 1
          #print(f"URNL {lineno} {regid} New location {loc_name}")

      if not location:
        print(f"URXL No location for {lineno} {regid}")

      gathering = Gathering.objects.filter(location = location).first()
      if not gathering:
        gathering = Gathering(
          regid=regid,
          gathering_type='STRK', # FIXME
          location=location,
          start_date=edate,
          end_date=edate)
        #print(f"Adding gathering {gathering}")
        gathering.save() 
        counter['Gathering'] += 1
        #print(f"URGC {lineno} {regid} Gathering created")

      belong = Gathering_Belong.objects.filter(regid = regid)
      if not belong:
        belong = Gathering_Belong(regid=regid, gathering=gathering)
        belong.save()
        counter['Gathering_Belong'] += 1
        #print(f"URGB {lineno} {regid} Gathering_Belong created")

      witness = Gathering_Witness.objects.filter(
        gathering = gathering,
        date = edate).first()
      if not witness:
        witness = Gathering_Witness(
          gathering = gathering, 
          date = edate)
        counter['Gathering_Witness'] += 1
        #print(f"URWC {lineno} {regid} Witness created")

      # Compare if newer
      rec_updated = get_update_timestamp(rec.get('RUPD'))
      db_updated = get_update_timestamp(witness.updated)
      if rec_updated > db_updated:
        revnum = '0' + rec.get('REVNUM','0')
        revnum = revnum.replace(',', '').replace(' ', '')
        witness.participants = int(revnum)
        witness.proof_url = rec.get('REVPROOF','')
        witness.save()
        counter['Witness Updated'] += 1
        #print(f"URUP {lineno}/{line_count} {regid} Witness updated")
      else:
        counter['Witness Not Updated'] += 1

      counter['Completed'] += 1
    except Exception as e:
      print(f"URXX === Exception on {lineno} updated recs:\n{e}")
  print(f"URDN {lineno} records results: {counter}")