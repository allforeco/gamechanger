from .models import Location, Gathering, Gathering_Witness

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
    rid = rec.get('RID', None)
    edate = rec.get('EDATE', None)
    if not rid or not edate:
      continue

    try:
      if not rec.get('GLOC'):
        location = Location.objects.filter(name = 'Unknown Place')
        if not location:
          location = Location(name = 'Unknown Place')
          location.save()
      else:
        location = Location.objects.filter(name = rec.get('GLOC')[:25])
        if location:
          location = location.first()
        else:
          location = Location(name = rec.get('GLOC')[:25])
          print(f"Adding location {location}")
          location.save()

      gathering = Gathering.objects.filter(regid = rid)
      if gathering:
        gathering = gathering.first()
      else:
        gathering = Gathering(
          regid=rid,
          gathering_type='STRK', # FIXME
          location=location,
          start_date_time=edate,
          end_date_time=edate)
        print(f"Adding gathering {gathering}")
        gathering.save()

      witness = Gathering_Witness.objects.filter(
        gathering = gathering,
        date = edate)
      if witness:
        witness = witness.first()

        # FIXME: Compare if newer
      else:
        witness = Gathering_Witness(
          gathering = gathering, 
          date = edate)
      witness.participants = int('0'+rec.get('REVNUM','0'))
      witness.proof_url = rec.get('REVPROOF','')
      witness.save()
      count += 1
    except Exception as e:
      print(f"=== Exception on {count}:\n{e}")
  return count