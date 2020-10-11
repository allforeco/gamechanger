import datetime
from .models import Location, Gathering, Gathering_Belong, Gathering_Witness

def get_update_timestamp(timestr):
  if timestr:
    try:
      return datetime.datetime.strptime(timestr, "%Y-%m-%dT%H:%M:%S")
    except:
      pass
  long_ago = datetime.datetime(1970, 1, 1, 0, 0, 0, 0)
  return long_ago

def update_reg(regs):
  count = 0
  doctype = regs[0][0]
  if doctype != 'FFF RegID':
    return 0

  headers = regs[1] # RID,RUPD,GLOC,EDATE,EENDDATE,REVNUM,REVPROOF
  for line in regs[2:]:
    rec = {}
    for col, val in enumerate(line):
      rec[headers[col]] = val
    regid = rec.get('RID', None)
    edate = rec.get('EDATE', None)
    if not regid or not edate:
      continue

    try:
      max_length = Location._meta.get_field('name').max_length
      loc_name = rec.get('GLOC','')[:max_length]
      if not loc_name:
        location = Location.objects.filter(name = 'Unknown Place')
        if not location:
          location = Location(name = 'Unknown Place')
          location.save()
      else:
        location = Location.objects.filter(name = loc_name).first()
        if not location:
          location = Location(name = loc_name)
          #print(f"Adding location {location}")
          location.save()

      if not location:
        print("No location for {regid}")

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

        if gathering.regid == "9CDWtj1J":
          print(f"Stockholm new: {Gathering.objects.filter(regid='9CDWtj1J').first().__dict__}")

      else:
        if gathering.regid == "9CDWtj1J":
          print(f"Stockholm exi: {Gathering.objects.filter(regid='9CDWtj1J').first().__dict__}")



      belong = Gathering_Belong.objects.filter(regid = regid)
      if not belong:
        belong = Gathering_Belong(regid=regid, gathering=gathering)
        belong.save()

      witness = Gathering_Witness.objects.filter(
        gathering = gathering,
        date = edate).first()
      if not witness:
        witness = Gathering_Witness(
          gathering = gathering, 
          date = edate)

      # Compare if newer
      rec_updated = get_update_timestamp(rec.get('RUPD'))
      db_updated = get_update_timestamp(witness.updated)
      if rec_updated >= db_updated:
        revnum = '0' + rec.get('REVNUM','0')
        revnum = revnum.replace(',', '').replace(' ', '')
        witness.participants = int(revnum)
        witness.proof_url = rec.get('REVPROOF','')
        witness.save()

      count += 1
    except Exception as e:
      print(f"=== Exception on {count}:\n{e}")
  return count