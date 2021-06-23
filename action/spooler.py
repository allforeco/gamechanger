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
from .models import Country, Location, Gathering, Gathering_Belong, Gathering_Witness, Organization
from .push_notifier import Push_Notifier

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
  print(f"UCLN unused places cleanup")
  try:
    cleanup_locations()
  except Exception as ex:
    print(f"UCLN top level exception: {ex}")
  print(f"UCLN unused places cleanup done")

def cleanup_locations():
  last_cleanup_log_name = "/var/log/gamechanger-spooler/last_cleanup.log"
  with open(last_cleanup_log_name, "w") as last_cleanup_log:
    print(f"Action spooler cleanup log taken on {datetime.datetime.ctime(datetime.datetime.utcnow())}", file=last_cleanup_log)

    # Initally all locations are candidates for dropping
    dropset = set(Location.objects.all())
    # Keep all locations that have gatherings in them
    print(f"UCRG go through {Gathering.objects.count()} gatherings")
    print(f"UCRG go through {Gathering.objects.count()} gatherings", file=last_cleanup_log)
    for gat in Gathering.objects.all():
      loc = gat.location
      # Keep all locations that are parents of the location with a gathering
      max_depth = 20
      while loc and loc in dropset:
        dropset.remove(loc)
        loc = loc.in_location
        max_depth -= 1
        if max_depth <= 0:
          print(f"UCRG location loop detected for {loc}")
          print(f"UCRG location loop detected for {loc}", file=last_cleanup_log)
          break

    print(f"UCRG {len(dropset)} locations are not referenced by any gatherings")
    print(f"UCRG {len(dropset)} locations are not referenced by any gatherings", file=last_cleanup_log)

    while dropset:
      print(f"UCRS Starting drop round with {len(dropset)} locations remaining", file=last_cleanup_log)
      next_dropset = set()
      progress = False
      for droploc in dropset:
        try:
          droploc.delete()
          print(f"UCRD dropped {droploc}", file=last_cleanup_log)
          progress = True
        except:
          print(f"UCRR {droploc} still referenced, dropping later", file=last_cleanup_log)
          next_dropset.add(droploc)
      if not progress:
        print(f"UCRX no progress with {len(dropset)} locations remaining", file=last_cleanup_log)
        break
      dropset = next_dropset

    print(f"UCRG done")
    print(f"UCRG done", file=last_cleanup_log)

def get_update_timestamp(timeinfo):
  if isinstance(timeinfo, datetime.datetime):
    return timeinfo.replace(tzinfo=datetime.timezone.utc)
  if isinstance(timeinfo, str):
    try:
      return datetime.datetime.strptime(timeinfo,"%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc)
    except:
      pass
  long_ago = datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc)
  return long_ago

def update_reg(regs):
  print("UREG Updating regid registry")
  last_import_log_name = "/var/log/gamechanger-spooler/last_import.log"
  with open(last_import_log_name, "w") as last_import_log:
    print(f"Action spooler update_reg log taken on {datetime.datetime.ctime(datetime.datetime.utcnow())}", file=last_import_log)
    print(f"ULOG Writing update_reg log to {last_import_log_name}")

    headers = regs[0] # RID,RUPD,GLOC,GLAT,GLON,CORG2,EDATE,EENDDATE,REVNUM,REVPROOF,RSOURCE,ETYPE,EFREQ,ETIME,ELINK
    print(f"URHD Read headers {headers}")
    line_count = len(regs)
    counter = {'Completed':0, 'Country':0, 'State':0, 'Region':0, 'Place':0,
               'Coords':0, 'Gathering':0, 'Gathering_Belong':0, 
               'Gathering_Witness':0, 'Witness Updated':0, 'Witness Not Updated':0,
               'Organization':0}
    for lineno, line in enumerate(regs[1:], 1):
      if lineno % 1000 == 1:
        print(f"URCT {lineno-1} {counter}")

      rec = {}
      for col, val in enumerate(line):
        rec[headers[col]] = val
      regid = rec.get('RID', None)
      edate = rec.get('EDATE', None)
      eenddate = rec.get('EENDDATE', None)
      etype_raw = rec.get('ETYPE', 'Strike')
      etype = Gathering.get_gathering_type_code(etype_raw)
      if not regid or not edate:
        print(f"{lineno} missing regid {regid} or edate {edate}", file=last_import_log)
        print(f"URBR Skipping record {lineno} {regid} {edate}")
        continue

      try:
        location = None
        country = None
        state = None
        region = None
        place = None
        max_length = Location._meta.get_field('name').max_length
        loc_name = rec.get('GLOC','')[:max_length]
        if not loc_name:
          loc_name = 'Unknown Place'
          location = Location.objects.filter(name = loc_name).first()
          if not location:
            location = Location(name = loc_name)
            location.save()
          print(f"{lineno} {regid} new location {location}", file=last_import_log)
          print(f"URUL {lineno} {regid} {loc_name}")
        else:
          (country_name, state_name, region_name, place_name, zip_code) = Location.split_location_name(loc_name)
          country = Location.objects.filter(name=country_name, in_location__isnull=True).first()
          if not country:
            # Allow for now, close country creation soon
            country = Country(name=country_name)
            country.save()
            try:
              country = Location(name=country_name)
              country.save()
              counter['Country'] += 1
              print(f"{lineno} {regid} new country {country}", file=last_import_log)
            except:
              pass
          parent_loc = country
          if state_name:
            state = Location.objects.filter(name=state_name, in_location=parent_loc).first()
            if not state:
              # Allow for now, close state creation soon
              state = Location(name=state_name, in_location=parent_loc)
              state.save()
              counter['State'] += 1
              print(f"{lineno} {regid} new state {state}", file=last_import_log)
            parent_loc = state
          if region_name:
            region = Location.objects.filter(name=region_name, in_location=parent_loc).first()
            if not region:
              region = Location(name=region_name, in_location=parent_loc)
              region.save()
              counter['Region'] += 1
              print(f"{lineno} {regid} new region {region}", file=last_import_log)
            parent_loc = region
          if place_name:
            place = Location.objects.filter(name=place_name, in_location=parent_loc).first()
            if not place:
              place = Location(name=place_name, in_location=parent_loc)
              place.save()
              counter['Place'] += 1
              print(f"{lineno} {regid} new place {place}", file=last_import_log)
            if not place.lat:
              place.lat = rec.get('GLAT')
              place.lon = rec.get('GLON')
              place.zip_code = zip_code
              place.save()
              counter['Coords'] += 1
              print(f"{lineno} {regid} new coords", file=last_import_log)
            location = place
        if not location:
          location = parent_loc
          print(f"URXL No place for {lineno} {regid}")
          print(f"{lineno} {regid} missing location {loc_name} in {location}", file=last_import_log)

        organization = None
        org_name = rec.get('CORG2')
        if org_name:
          org_name = org_name[:25]# FIXME: Max length 25 chars; Find better ways to do this?
          organization = Organization.objects.filter(
            name = org_name).first()
          if not organization:
            organization = Organization(
              name = org_name)
            organization.save()
            counter['Organization'] += 1
            print(f"{lineno} {regid} new organization {org_name}", file=last_import_log)

        gathering = Gathering.objects.filter(location=location, regid=regid).first()
        if not gathering:
          gathering = Gathering(
            regid=regid,
            gathering_type=etype,
            location=location,
            start_date=edate,
            end_date=eenddate)
          
          gathering.save()
          if organization:
            gathering.organizations.add(organization)
            gathering.save()
          #print(f"Adding gathering {gathering}")

          counter['Gathering'] += 1
          print(f"{lineno} {regid} new gathering {gathering} {gathering.__dict__}", file=last_import_log)
          #print(f"URGC {lineno} {regid} Gathering created")
        else:
          dirty = False
          if gathering.gathering_type != etype:
            gathering.gathering_type = etype
            dirty = True
          if gathering.end_date != eenddate:
            gathering.end_date = eenddate
            dirty = True
          if dirty:
            print(f"{lineno} {regid} updated gathering {gathering.gathering_type} {gathering.end_date}", file=last_import_log)
            gathering.save()
          print(f"{lineno} {regid} existing gathering {gathering} {gathering.regid} {gathering.location}", file=last_import_log)

        belong = Gathering_Belong.objects.filter(regid = regid).first()
        if not belong:
          belong = Gathering_Belong(regid=regid, gathering=gathering)
          belong.save()
          counter['Gathering_Belong'] += 1
          print(f"{lineno} {regid} new belong {belong}", file=last_import_log)
          #print(f"URGB {lineno} {regid} Gathering_Belong created")

        if organization and organization not in belong.gathering.organizations.all():
          belong.gathering.organizations.add(organization)
          belong.gathering.save() 
          print(f"{lineno} {regid} added organization {organization} to gathering {belong.gathering.regid} {belong.gathering.location}", file=last_import_log)

        long_ago = datetime.datetime(1970,1,1,tzinfo=datetime.timezone.utc)
        db_updated = long_ago
        witness_queryobj = Gathering_Witness.objects.filter(
          gathering = Gathering.objects.get(regid=belong.gathering.regid),
          date = edate)
        witness = witness_queryobj.first()
        print(f"{lineno} {regid} {edate} witnesses count {witness_queryobj.count()} first: {witness.__dict__ if witness else None}", file=last_import_log)
        if not witness:
          witness = Gathering_Witness(
            gathering = Gathering.objects.get(regid=belong.gathering.regid),
            date = edate,
            updated = long_ago)
          witness.save()
          counter['Gathering_Witness'] += 1
          print(f"{lineno} {regid} new witness {gathering}=>{belong.gathering.regid}:{edate}", file=last_import_log)
          #print(f"URWC {lineno} {regid} Witness created")
        else:
          db_updated = get_update_timestamp(witness.updated)
          print(f"{lineno} {regid} db_updated {db_updated} {db_updated.tzinfo} {witness.updated}", file=last_import_log)

        if organization:
          if witness.organization != organization:
            witness.organization = organization
            witness.save()
            print(f"URWO {lineno} {regid} Witness organization updated to {organization}")

        # Compare if newer
        rec_updated = get_update_timestamp(rec.get('RUPD'))
        print(f"{lineno} {regid} rec_updated {rec_updated} {rec_updated.tzinfo}", file=last_import_log)
        print(f"{lineno} {regid} participants {witness.participants} {rec.get('REVNUM','0')}", file=last_import_log)
        if rec_updated > db_updated or db_updated == long_ago:
          revnum = '0' + rec.get('REVNUM','0')
          revnum = revnum.replace(',', '').replace(' ', '')
          witness.participants = int(revnum)
          witness.proof_url = rec.get('REVPROOF','')
          witness.updated = rec_updated
          witness.save()
          counter['Witness Updated'] += 1
          print(f"{lineno} {regid} updated witness {witness}, {rec_updated} > {db_updated}", file=last_import_log)
          #print(f"URUP {lineno}/{line_count} {regid} Witness updated")
        else:
          counter['Witness Not Updated'] += 1
          print(f"{lineno} {regid} no change to witness, {rec_updated} <= {db_updated}", file=last_import_log)

        counter['Completed'] += 1
        print(f"{lineno} {regid} completed {location} in {location.in_location}: {place} {region} {state} {country} {gathering} {belong} {witness} <- '{loc_name}'", file=last_import_log)
      except Exception as e:
        print(f"{lineno} {regid} exception {e}", file=last_import_log)
        print(f"URXX === Exception on {lineno} updated recs:\n{e}")
    print(f"URDN {lineno} records results: {counter}")
    if lineno:
      if counter['Completed'] < lineno * 0.90:
        Push_Notifier.push(
          title="Gamechanger failed update",
          message=f"{lineno} records resulted in {counter}",
        )
      else:
        Push_Notifier.push(
          title="Gamechanger updated",
          message=f"{lineno} records resulted in {counter}",
      )
