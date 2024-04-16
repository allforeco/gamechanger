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

import datetime, io, csv, traceback

from .models import Country, Location, Gathering, Gathering_Belong, Gathering_Witness, Organization
from .push_notifier import Push_Notifier
from .map_sync import to_fff

'''
===Automaticly read coffer data
???
'''

static_location_file = "/var/www/gamechanger.eco/static/cached_locations.htmlbody"

try:
  import uwsgi
  from uwsgidecorators import spool
  print(f"INIT uWSGI imported in spooler")

  @spool
  def action_spooler(req):
    task = req.get('task')
    print(f"SPOL Gamechanger spooler running, got {task} job")
    body = req.get('body')
    if body:
      print(f"SSMP Body len {len(body)} sample '{str(body)[:100]}'...")
    if task == 'upload' and body:
      task_update_reg(body)
    elif task == 'mapsync-full':
      sync_to_fff()
    else:
      print('SUNK Unknown spool job type')
    print(f"SEND Gamechanger spooler job complete")
    return uwsgi.SPOOL_OK
except ImportError:
  uwsgi = None
  print(f"INIT uWSGI not found in spooleSEND Gamechanger r")
  
  def action_nospooler(body):
    task_update_reg(body, "last_import.log", "last_cleanup.log")
  

def task_update_reg(body, import_log=None, cleanup_log=None):
  reg_file = io.StringIO(body)
  reg_reader = csv.reader(reg_file, delimiter=',')
  doctype_line = reg_reader.__next__()
  doctype = doctype_line[0]
  if not doctype.startswith('FFF RegID'):
    print(f"URDT Bad doctype '{doctype}'")
    if (uwsgi):
      return uwsgi.SPOOL_OK
    else:
      return

  reg_list = [line for line in reg_reader]
  count_of = len(reg_list)
  print(f"URLN {count_of} place definitions to process")
  print(f"STUR {reg_file}...")
  update_reg(reg_list, import_log)
  print(f"URES place definitions processed")
  print(f"UCLN unused places cleanup")
  try:
    cleanup_locations(cleanup_log)
    loc_map = generate_static_location_list(cleanup_log)
    write_static_location_countries(cleanup_log, loc_map)

  except Exception as ex:
    print(f"UCLN top level exception: {ex}")
  print(f"UCLN unused places cleanup done")

def logprint(log, s):
  print(s)
  print(s, file=log)

def generate_static_location_list(log):
  non_roots = Location.objects.filter(in_location_id__isnull=False)
  logprint(log,f"LLL0 Generating static location list, {len(non_roots)} items")
  loc_root_map = {}
  loc_map = {}
  for nr,loc in enumerate(non_roots):
    if nr%100 == 0:
      logprint(log,f"LLL1 Generating static location list, item {nr}")
    ploc = loc_root_map.get(loc.id, None)
    if not ploc:
      ploc = loc
      loops_left = 10
      while ploc.in_location and loops_left:
        ploc = ploc.in_location
        loops_left -= 1
      if not loops_left:
        logprint(log,f"LLLL Location nesting too deep for loc {loc} id {loc.id}, skipping")
        continue
    loc_root_map[loc.id]=ploc
    loc_map[ploc.id] = loc_map.get(ploc.id,[]) + [loc]
  return loc_map

def write_static_location_countries(log, loc_map):
  with open(static_location_file, "w") as stat:
    roots = Location.objects.filter(in_location_id__isnull=True).order_by('name')
    for root in roots:
      try:
        if not root.name or root.id not in loc_map:
          continue
        logprint(log,f"LLCO Country {root.name}")
        members = [(loc.name, loc.id) for loc in loc_map[root.id]]
        members.sort(key = lambda x: x[0])
        logprint(log,f"LLCL Country locations {[(member[0], member[1]) for member in members]}")
        stat.write(f"""
                <tr>
                <td style="text-align: center; margin-top: 0px; vertical-align: top;">
                  <a href="/action/geo/{root.id}/">{root.name}</a>
                </td>
                <td>
                  <ul style="float: left; margin-bottom: 1em; width: 100%;">""")
        stat.write("".join([f"""
                    <li style="float: left; margin-left: 1.5em; margin-bottom: 0.5em;">
                      <a href="/action/geo/{member[1]}/">{member[0]}</a>
                    </li>""" for member in members]))
        stat.write(f"""
                  </ul>
                </td>
              </tr>""")
      except:
        logprint(log,f"LLFX Country {root.name} failed")
  logprint(log,f"LLL9 Generated static location list")

def cleanup_locations(cleanup_log = None):
  def drop_orphans(log):
    # Initally all locations are candidates for dropping
    dropset = set(Location.objects.all())
    # Keep all locations that have gatherings in them
    logprint(log,f"UCRG go through {Gathering.objects.count()} gatherings")
    for gat in Gathering.objects.all():
      loc = gat.location
      # Keep all locations that are parents of the location with a gathering
      max_depth = 20
      while loc and loc in dropset:
        dropset.remove(loc)
        loc = loc.in_location
        max_depth -= 1
        if max_depth <= 0:
          logprint(log, f"UCRG location loop detected for {loc}")
          break

    logprint(log,f"UCRG {len(dropset)} locations are not referenced by any gatherings")

    while dropset:
      logprint(log,f"UCRS Starting drop round with {len(dropset)} locations remaining")
      next_dropset = set()
      progress = False
      for droploc in dropset:
        try:
          droploc.delete()
          logprint(log,f"UCRD dropped {droploc}")
          progress = True
        except:
          logprint(log,f"UCRR {droploc} still referenced, dropping later")
          next_dropset.add(droploc)
      if not progress:
        logprint(log,f"UCRX no progress with {len(dropset)} locations remaining")
        break
      dropset = next_dropset

  last_cleanup_log_name = "/var/log/gamechanger-spooler/last_cleanup.log"
  if cleanup_log:
    last_cleanup_log_name = cleanup_log
  with open(last_cleanup_log_name, "w") as log:
    logprint(log,f"Action spooler cleanup log taken on {datetime.datetime.ctime(datetime.datetime.utcnow())}")
    drop_orphans(log)
    #remap_duplicates(log)
    #remap_loops(log)
    #remap_nameless(log)
    #rename_bad_names(log)
    logprint(log,f"UCRG done")

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

def update_reg(regs, import_log = None):
  print("UREG Updating regid registry")
  last_import_log_name = "/var/log/gamechanger-spooler/last_import.log"
  if import_log:
    last_import_log_name = import_log
    
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
      
      print(f"M {lineno} '{line}'")

      rec = {}
      for col, val in enumerate(line):
        rec[headers[col]] = val
      regid = rec.get('RID', None)
      edate = rec.get('EDATE', None)
      eenddate = rec.get('EENDDATE', None)
      etype_raw = rec.get('ETYPE', 'Strike')
      etype = Gathering.get_gathering_type_code(etype_raw)
      eaddress = rec.get('ELOCATION', None)[:Gathering._meta.get_field('address').max_length]
      etime = rec.get('ETIME', None)[:Gathering._meta.get_field('time').max_length]
      cname = rec.get('CNAME', None)[:Gathering._meta.get_field('contact_name').max_length]
      cemail = rec.get('CEMAIL', None)[:Gathering._meta.get_field('contact_email').max_length]
      cphone = rec.get('CPHONE', None)[:Gathering._meta.get_field('contact_phone').max_length]
      cnotes = rec.get('CNOTES', None)[:Gathering._meta.get_field('contact_notes').max_length]

      if not regid or not edate:
        print(f"{lineno} missing regid {regid} or edate {edate}", file=last_import_log)
        print(f"URBR Skipping record {lineno} {regid} {edate}")
        continue

      try:
        location = None
        #country = None
        state = None
        region = None
        place = None
        max_length = Location._meta.get_field('name').max_length
        loc_name = rec.get('GLOC','')[:max_length]
        if not loc_name:
          #loc_name = 'Unknown Place'
          #location = Location.objects.filter(name = loc_name).first()
          location = Location.Unknown()
          if not location:
            location = Location(name = loc_name)
            location.save()
          print(f"{lineno} {regid} new location {location}", file=last_import_log)
          print(f"URUL {lineno} {regid} {loc_name}")
        else:
          (country_name, state_name, region_name, place_name, zip_code) = Location.split_location_name(loc_name)
          #country = Location.objects.filter(name=country_name, in_location__isnull=True).first()
          countryLocation = location.country()
          if not countryLocation:
            # Allow for now, close country creation soon
            #country = Country(name=country_name)
            #country.save()
            country = Country.generateNew(country_name)
            try:
              countryLocation = Location(name=country_name, in_location=None, in_country=country)
              countryLocation.save()
              counter['Country'] += 1
              print(f"{lineno} {regid} new country {country}", file=last_import_log)
            except:
              countryLocation = Location.Unknown()
              pass
          parent_loc = countryLocation
          if state_name:
            state = Location.objects.filter(name=state_name, in_location=parent_loc).first()
            if not state:
              # Allow for now, close state creation soon
              state = Location(name=state_name, in_location=parent_loc, in_country=country)
              state.save()
              counter['State'] += 1
              print(f"{lineno} {regid} new state {state}", file=last_import_log)
            parent_loc = state
          if region_name:
            region = Location.objects.filter(name=region_name, in_location=parent_loc).first()
            if not region:
              region = Location(name=region_name, in_location=parent_loc, in_country=country)
              region.save()
              counter['Region'] += 1
              print(f"{lineno} {regid} new region {region}", file=last_import_log)
            parent_loc = region
          if place_name:
            place = Location.objects.filter(name=place_name, in_location=parent_loc).first()
            if not place:
              place = Location(name=place_name, in_location=parent_loc, in_country=country)
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
          org_name = org_name[:Organization._meta.get_field('name').max_length]# FIXME: Max length 25 chars; Find better ways to do this?
          organization = Organization.objects.filter(name = org_name).first()
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
            end_date=eenddate,
            address=eaddress,
            time=etime,
            contact_name=cname,
            contact_email=cemail,
            contact_phone=cphone,
            contact_notes=cnotes)
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
          if gathering.contact_name != cname:
            gathering.contact_name = cname
            dirty = True
          if gathering.contact_phone != cphone:
            gathering.contact_phone = cphone
            dirty = True
          if gathering.contact_email != cemail:
            gathering.contact_email = cemail
            dirty = True
          if gathering.contact_notes != cnotes:
            gathering.contact_notes = cnotes
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
          witness_belong = Gathering.objects.get(regid=belong.gathering.regid)
          if witness_belong:
            witness = Gathering_Witness(
              gathering = witness_belong,
              date = edate,
              updated = long_ago)
            witness.save()
            counter['Gathering_Witness'] += 1
            print(f"{lineno} {regid} {edate} new witness {gathering}=>{belong.gathering.regid}:{edate}", file=last_import_log)
            #print(f"URWC {lineno} {regid} Witness created")
          else:
            print(f"{lineno} {regid} {edate} Broken witness {gathering}=>{belong.gathering.regid}:{edate}", file=last_import_log)
        else:
          db_updated = get_update_timestamp(witness.updated)
          print(f"{lineno} {regid} {edate} db_updated {db_updated} {db_updated.tzinfo} {witness.updated}", file=last_import_log)

        if organization:
          if not witness.organization:
            witness.organization = organization
            witness.save()
            print(f"URWO {lineno} {regid} {edate} Witness organization updated to {organization}")

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
        traceback.print_exc()
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
