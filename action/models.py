#   Gamechanger Action Models
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

from django.db import models
from django.contrib.auth.models import User
from action.static_lists import valid_location_ids
import pycountry, datetime, random, string, itertools
#from .cookie_profile import CookieProfile


'''
___Database registered Locations
'''
class Location(models.Model):
  def __str__(self):
    out = f"{self.name}"
    try:
      if self.id != self.country_location().id:
        if self.id != self.state_location().id:
          out += f", {self.state_location().name}"
      if self.in_country.id != Country.UNKNOWN:
        out += f", {self.in_country.code}"
    except:
      pass
    
    return out

  name = models.CharField(max_length=100)
  in_country = models.ForeignKey('Country', on_delete=models.CASCADE, blank=True, null=True)
  in_location = models.ForeignKey('Location', on_delete=models.PROTECT, blank=True, null=True)
  zip_code = models.CharField(max_length=12, blank=True, null=True)
  lat = models.FloatField(blank=True, null=True)
  lon = models.FloatField(blank=True, null=True)
  #google_name = models.CharField(max_length=255, null=True, blank=True)
  #verified = models.ForeignKey("Verification", on_delete=models.CASCADE, blank=True, null=True)
  creation_details = models.CharField(max_length=500, blank=True, null=True)
  google_metadata = models.CharField(max_length=2048,blank=True, null=True)

  '''
  ___stringify coordinates
  '''
  def str_lat_lon(self):
    return f"({self.lat},{self.lon})"

  def location_range_depth(self):
    return 8
  
  '''
  ___location integrity by
  ___country and coordinate validity
  '''
  def tracable(self):
    t=0
    if self.in_country != Country.objects.get(id=Country.UNKNOWN): t+=1
    if self.lat != None and self.lon != None: t+=1
    return t

  UNKNOWN = 0
  def Unknown():
    if Location.objects.filter(id=Location.UNKNOWN).exists():
      return Location.objects.filter(id=Location.UNKNOWN).first()
    else:
      return None

  def SETUP_Unknown():
    if not Location.Unknown():
      unknown = Location()
      unknown.id = Location.UNKNOWN
      unknown.name = "Unknown"
      unknown.in_country = Country.Unknown()
      unknown.zip_code = None
      unknown.lat = None
      unknown.lon = None
      unknown.creation_details = "SETUP"
      unknown.save()
      unknown.in_location = Location.Unknown()
      unknown.save()
  
  
  #_DUPLICATEEXCEPTION = {
  #  6111: [54138],
  #  8181: [54776, 54778],
  #  } #GB: UK
  def Duplicate_is(location):
    return Location.Duplicate_get(location).exists()
  
  def Duplicate_get(location):
    r = Location.objects.none()
    lb = Location_Belong.objects.filter(duplicate=location).first()
    if lb:
      #print("Duplicate Exception", lb)
      lbs = Location_Belong.objects.filter(prime=lb.prime)
      r |= Location.objects.exclude(id=location.id).filter(id=lb.prime.id)
      for l in lbs:
        r |= Location.objects.filter(id=l.duplicate.id)
    
    lb = Location_Belong.objects.filter(prime=location).first()
    if lb:
      lbs = Location_Belong.objects.filter(prime=lb.prime)
      #print("Duplicate Exception", lbs)
      for l in lbs:
        r |= Location.objects.filter(id=l.duplicate.id)

    r |= Location.objects.exclude(id=location.id).filter(name=location.name, in_location=location.in_location, in_country=location.in_country)
    return r 
  
  def Duplicate_is_prime(location):
    return location == Location.Duplicate_get_prime(location)
  
  def Duplicate_get_prime(location):
    prime = None
    try:
      primeQ = Location.objects.filter(id=location.id)
      primeQ |= Location.Duplicate_get(location) # Location.objects.filter(name=location.name, in_location=location.in_location, in_country=location.in_country).first()
      prime = primeQ.order_by('id').first()
    except:
      pass
    return prime

  def Duplicate_clean(locations = [], gatherings = [], organizationcontacts = [] ):
    orcClean = 0
    gthClean = 0
    locClean = 0
    for location in locations:# or Location.objects.all():
      if location.in_location:
        if Location.Duplicate_is(location.in_location):
          if not Location.Duplicate_is_prime(location.in_location):
            print("DCL", location.in_location.id, Location.Duplicate_get_prime(location.in_location).id)
            location.in_location = Location.Duplicate_get_prime(location.in_location)
            location.save()
            locClean +=1

    for organizationcontact in organizationcontacts:# or OrganizationContact.objects.all():
      if organizationcontact.location:
        if Location.Duplicate_is(organizationcontact.location):
          if not Location.Duplicate_is_prime(organizationcontact.location):
            print("DCO", organizationcontact.location.id, Location.Duplicate_get_prime(organizationcontact.location).id)
            organizationcontact.location = Location.Duplicate_get_prime(organizationcontact.location)
            organizationcontact.save()
            orcClean+=1

    for gathering in gatherings:# or Gathering.objects.all():
      if gathering.location:
        if Location.Duplicate_is(gathering.location):
          if not Location.Duplicate_is_prime(gathering.location):
            print("DCG", gathering.location.id, Location.Duplicate_get_prime(gathering.location).id)
            gathering.location = Location.Duplicate_get_prime(gathering.location)
            gathering.save()
            gthClean +=1

    
    print(f"Clean orc: {orcClean} gth:{gthClean} loc:{locClean}")

  def all_delete(loopmax = 8):
    ls = Location.objects.exclude(id=Location.UNKNOWN).order_by('-id')
    for l in ls:
      try:
       l.delete()
      except:
        print("delete exception", l)
    
    if loopmax <= 0:
      print("delete exception, max recursion depth")
      return

    if len(ls) > 0:
      Location.all_delete(loopmax-1)

    print("Locations: ", Location.objects.all())

  '''
  ___location search
  ___order by name start->contains, searchterm q
  ___option include/exclude unknown country
  '''
  def search(q, option = 1):
    if option == 1:
      ls = Location.objects.all()
    else:
      ls = Location.objects.exclude(in_country=Country.Unknown())
    lsf = Location.objects.none()

    if q[2] == '!':
      for c in Country.objects.filter(code__iexact=q[0:2]):
        lsf |= Location.objects.filter(name=c.name)
    else:
      ls = ls.filter(name__icontains=q)

      for location in ls:
        if Location.Duplicate_is_prime(location):
          lsf |= Location.objects.filter(id=location.id)
          pass

    lout = lsf.filter(name__istartswith=q)
    lout |= lsf.exclude(name__istartswith=q)
    return lout.order_by('id')
  
  '''
  ___Get location of country
  '''
  def c_country_location(self):
    locations = Location.objects.filter(in_country=self.in_country, name=self.in_country.name)
    if locations.count() > 0:
      return locations.first()
    else:
      return Location.Unknown()
  
  '''
  ___finds toplocation as country
  '''
  def country_location(self):
    return self.in_location_list()[-1]

  def state_location(self):
    return self.in_location_list()[-2]
      
  def in_location_list(self):
    in_locations = [self]
    toplocation = self
    for i in range(self.location_range_depth()):
      if toplocation.in_location:
        if toplocation.in_location.id != Location.UNKNOWN:
          toplocation = toplocation.in_location
          in_locations.append(toplocation)
        else:
          return in_locations
      else:
        return in_locations

  '''
  ___
  '''
  @staticmethod
  def countries(generate = True):
    if generate:
      location_list = Location.objects.filter(lat__isnull=False)[:]
    else:
      location_list = Location.valid_ids(False)
    location_dict=dict()

    for location_id in location_list:
      locations = Location.objects.filter(id=location_id)
      if not locations:
        continue
      location = country = locations[0]
      try:
        for x in range(5):
          if country.in_location:
            country = country.in_location
          else:
            break
      except:
        print(f"LOLX {location} {country}")
        continue
      
      if country.name in location_dict:
        location_dict[country.name][2].append([location.name, location.id])
      else:
        location_dict.update({country.name:[country.name, country.id, list()]})
        location_dict[country.name][2].append([location.name, location.id])

    location_list = list(location_dict.values())
    
    return location_list

  '''DEPRICATED?
  ___calculates locations with integrity by calculating country
  ___option: generate or static list
  '''
  @staticmethod
  def valid_ids(generate = False):
    #generate = True
    if generate:
      location_list = Location.countries(True)
      location_id_list=list()

      for country in location_list:
        location_id_list.append(country[1])
        for location in country[2]:
          location_id_list.append(location[1])
      
      return location_id_list
    else:
      return valid_location_ids()

  '''
  ???testdata to test new location creation by google maps
  '''
  @staticmethod
  def _split_location_name_test():
    # Examples of location names received from Google Maps:
    for loc_name in [
      "Umeå, Sweden",
      "London, UK",
      "Boulder, CO, USA",
      "Niwot, CO 80503, USA",
      "Gettysburg, PA 17325, USA",
      "Brattleboro, VT 05301, USA",
      "Calgary, AB, Canada",
      "442 95 Hålta, Sweden",
      "23795 Bad Segeberg, Germany",
      "Adıyaman, Adıyaman Merkez/Adıyaman Province, Turkey",
      "Årsta, Enskede-Årsta-Vantör, Stockholm, Sweden",
      "39100 Bolzano, Province of Bolzano - South Tyrol, Italy",
      "04016 Sabaudia LT, Italy",
      "37068 Vigasio, VR, Italy",
      "St Neots, Saint Neots PE19, UK",
      "Hebden Bridge HX7, UK",
      "Abu Dhabi, United Arab Emirates",
      "Waurn Ponds VIC 3216, Australia",
      "Dungog NSW 2420, Australia",
      "Ravenshoe QLD 4888, Australia",
      "Gibraltar",
      "Poza Rica de Hidalgo, Ver., Mexico",
      "Mumbai, Maharashtra, India",
      "Skopje, Macedonia (FYROM)",
      "Gol ghar, Park Rd, Raja Ji Salai, Chajju Bagh, Patna, Bihar 800001, India",
    ]:
      print(f"Name '{loc_name}' => '{split_location_name(loc_name)}'")

  '''
  ???something google maps parser
  '''
  @staticmethod
  def split_location_name(loc_name):
    countries_with_states = [
      "USA",
      "Canada",
      "Australia",
      "India",
    ]
    countries_with_regions = [
      "Mexico",
      "Italy",
    ]
    def contains_number(word):
      for char in word:
        if char in "0123456789":
          return True
      return False
    zip_code = ""
    state_name = None
    region_name = None
    clean_parts = []
    parts = loc_name.split(",")
    parts.reverse()
    for part in parts:
      part = part.strip()
      words = []
      for word in part.split(" "):
        if contains_number(word):
          zip_code += word
          continue
        # Remove certain words from place names
        # (in order to remove duplicate locations with and without this word)
        if word.casefold() in ["municipality", "county"]: 
          continue
        words += [word]
      clean_parts += [" ".join(words)]
    if not zip_code:
      zip_code = None
    country_name = clean_parts.pop(0)
    if not clean_parts:
      return (country_name, None, None, None, zip_code)
    place_name = clean_parts.pop()
    last_word_in_place_name = place_name.split(" ")[-1]
    if last_word_in_place_name.isupper():
      place_name = place_name[:-(len(last_word_in_place_name)+1)]
      if country_name in countries_with_states:
        state_name = last_word_in_place_name
      elif country_name in countries_with_regions:
        region_name = last_word_in_place_name
    if not clean_parts:
      return (country_name, state_name, region_name, place_name, zip_code)
    if not state_name and country_name in countries_with_states:
      state_name = clean_parts.pop(0)
    if not clean_parts:
      return (country_name, state_name, region_name, place_name, zip_code)
    if not region_name:
      region_name = clean_parts.pop(0)
    if not clean_parts:
      return (country_name, state_name, region_name, place_name, zip_code)
    clean_parts.insert(0, place_name)
    place_name = ", ".join(clean_parts)
    return (country_name, state_name, region_name, place_name, zip_code)

  '''
  ???something google maps parser, location name
  '''
  @staticmethod
  def make_location_name(country_name, state_name=None, region_name=None, place_name=None, zip_code=None, joiner=", "):
    loc_name = country_name.strip()
    if state_name:
      loc_name = state_name + joiner + loc_name
    if region_name:
      loc_name = region_name + joiner + loc_name
    if place_name:
      loc_name = place_name + joiner + loc_name
    return loc_name

  '''
  ???
  '''
  @staticmethod
  def delete_all_unused(show=True,doit=False):
    total = 0
    to_delete = []
    for loc in Location.objects.all():
      cnt = Gathering.objects.filter(location=loc).count()
      cnt += Location.objects.filter(in_location=loc).count()
      if cnt == 0:
        total += 1
        if show:
          print(loc)
        if doit:
          to_delete += [loc]
    if to_delete:
      for loc in to_delete:
        loc.delete()
    if doit:
      print(f"{total} looped locations found and deleted")
    else:
      print(f"{total} looped locations found")

  '''
  ???
  '''
  @staticmethod
  def delete_all_loops(show=True,doit=False):
    total = 0
    to_delete = []
    for loc in Location.objects.all():
      parents = []
      while loc:
        if loc in parents:
          total += 1
          if show:
            print(f"{loc} in chain {parents}")
          if doit:
            to_delete += [loc]
          break
        parents += [loc]
        loc = loc.in_location
    if to_delete:
      for loc in to_delete:
        loc.delete()
    if doit:
      print(f"{total} looped locations found and deleted")
    else:
      print(f"{total} looped locations found")

class Location_Belong(models.Model):
  def __str__(self):
    return str(self.duplicate.id) + "=>" + str(self.prime.id)

  duplicate = models.OneToOneField(Location, on_delete=models.CASCADE, primary_key=True, editable=True)
  prime = models.ForeignKey(Location, on_delete=models.CASCADE,related_name="+")
  

'''
___database countries
'''
class Country(models.Model):
  def __str__(self):
    return f"{self.name}, {self.code}"

  name = models.CharField(max_length=50)
  phone_prefix = models.CharField(max_length=5, blank=True)
  #location = models.ForeignKey(Location, on_delete=models.CASCADE, blank=False, null=False)
  code = models.CharField(max_length=4, null=True, blank=True)
  flag = models.CharField(max_length=16, null=True, blank=True)

  '''
  ___pycountry data on self
  '''
  def pycy(self):
    return pycountry.countries.get(alpha_2=self.code)[0]
  
  UNKNOWN = 0
  def Unknown():
    if Country.objects.filter(id=Location.UNKNOWN).exists():
      return Country.objects.filter(id=Location.UNKNOWN).first()
    else:
      return None
  
  def SETUP_Unknown():
    if not Country.Unknown():
      unknown = Country()
      unknown.id = Country.UNKNOWN
      unknown.name = "Unknown"
      unknown.phone_prefix = 0
      unknown.code = "XX"
      unknown.flag = "🏳️"
      unknown.save()
  
  '''
  ___Get location of country
  '''
  def country_location(self):
    locations = Location.objects.filter(in_country=self, name=self.name, in_location=None)
    if locations.count() > 0:
      return locations.first()
    else:
      return Location.Unknown()

  '''
  ___Country search
  ___order by name start->contains, searchterm q
  ___option include/exclude unknown country
  '''
  def search(q, option = 0):
    if option == 1:
      csr = Country.objects.all()
    else:
      csr = Country.objects.exclude(id=Country.UNKNOWN)
    cs = csr.filter(code__iexact=q)
    cs |= csr.filter(name__icontains=q)

    cout = cs.filter(code__iexact=q)
    cout |= cs.filter(name__istartswith=q)
    cout |= cs.exclude(name__istartswith=q)
    return cout

  '''
  ___pycountry lookup
  '''
  def pycy_get(name):
    if name.upper() == "UK":
      name = "United Kingdom"
    pycy = None
    try:
      if pycountry.countries.get(alpha_2=name):
        pycy = pycountry.countries.get(alpha_2=name)
      elif pycountry.countries.get(alpha_3=name):
        pycy = pycountry.countries.get(alpha_3=name)
      elif pycountry.countries.get(name=name):
        pycy = pycountry.countries.get(name=name)
      elif pycountry.countries.get(official_name=name):
        pycy = pycountry.countries.get(official_name=name)
      elif pycountry.countries.search_fuzzy(name):
        #pycy = pycountry.countries.search_fuzzy(name)[0]
        pass
    except:
      pycy = None

    return pycy

  '''
  ___generate countries
  ___by location country calculation matching pycountry
  '''
  def generate(option = 0):
    print("generate")
    print_add = 0
    print_edit = 0
    print_option = 0
    
    if option == 1:
      Country.objects.all().delete()
      print_option = 1

    if option == 2:
      Location.objects.all().in_country=None
      print_option = 2

    Country.SETUP_Unknown()

    for location in Location.objects.all():
      l = location.country_location()
      l.in_location=None
      l.save()
      if l:
        pycy=Country.pycy_get(l.name)
      else:
        pycy=None
      if pycy != None:
        if Country.objects.filter(name=pycy.name).exists():
          c = Country.objects.filter(name=pycy.name).first()
          if c.code == None or c.flag == None:
            c.code = pycy.alpha_2
            c.flag = pycy.flag
            c.save()
            print_edit += 1
          location.in_country = c
        else:
          c = Country()
          c.name = pycy.name
          c.code = pycy.alpha_2
          c.flag = pycy.flag
          c.save()
          print_add += 1
          location.in_country = c
      else:
        location.in_country = Country.Unknown()
      
      location.save()

    print(f"New: {print_add}, Edit: {print_edit}, reset: {print_option}")

  def generateNew(name):
    c=Country.Unknown()
    pycy=Country.pycy_get(name)
    if pycy:
      if not Country.objects.filter(name=pycy.name):
        c = Country(name=pycy.name, code=pycy.alpha_2, flag=pycy.flag)
        c.save()

    return c

  '''
  ___as set
  '''
  @staticmethod
  def as_set(static):
    return {country.name for country in Country.objects.all()}

'''
___database organizations
'''
class Organization(models.Model):
  def __str__(self):
    return self.name

  name = models.CharField(max_length=50, unique=True)
  verified = models.IntegerField(default=0)
  #primary_location = models.ForeignKey(Location, on_delete=models.CASCADE, blank=True, null=True)
  #contacts = models.ManyToManyField(Contact, blank=True)
  #verified = models.ForeignKey(Verification, on_delete=models.CASCADE, editable=False)

  '''
  ___organization search
  ___order by name start->contains, searchterm q
  ___option include/exclude unknown country
  '''
  def search(q, option = 0):
    if option == 1:
      os = Organization.objects.all()
    else:
      os = Organization.objects.exclude(id=Organization.UNKNOWN)
    os = os.filter(name__icontains=q)
    oout = os.filter(name__istartswith=q)
    oout |= os.exclude(name__istartswith=q)
    return oout

  UNKNOWN = 0
  def Unknown():
    if Organization.objects.filter(id=Location.UNKNOWN).exists():
      return Organization.objects.filter(id=Location.UNKNOWN).first()
    else:
      return None
  
  def SETUP_Unknown():
    if not Organization.Unknown():
      unknown = Organization()
      unknown.id = Organization.UNKNOWN
      unknown.name = "Unknown"
      unknown.verified = 10
      unknown.save()

'''
___database contact information
___to match with organizations, locations
'''
class OrganizationContact(models.Model):
  def __str__(self):
    return f"{self.organization} [{self.contacttype} \"{self.address}\"]"

  '''
  ___recognized media
  '''
  OTHER="OTHR"
  EMAIL="MAIL"
  PHONE="PHON"
  WEBSITE="WEBS"
  YOUTUBE="YOUT"
  TWITTER="TWTR"
  FACEBOOK="FCBK"
  INSTAGRAM="INSG"
  LINKEDIN="LNIN"
  VIMEO="VIME"
  WHATSAPP="WHAP"
  TELEGRAM="TLGM"
  DISCORD="DCRD"
  SLACK="SLAK"

  _contact_type_choices =[
    (OTHER, "Other Contact Address"),
    (EMAIL, "Email Address"),
    (PHONE, "Phone Number"),
    (WEBSITE, "Organization Website URL"),
    (YOUTUBE, "Youtube URL"),
    (TWITTER, "X (formerly twitter) URL"),
    (FACEBOOK, "Facebook URL"),
    (INSTAGRAM, "Instagram URL"),
    (LINKEDIN, "LinkedIn URL"), #!!!
    (VIMEO, "Vimeo URL"), #!!!
    (WHATSAPP, "WhatsApp group URL"), #!!!
    (TELEGRAM, "Telegram group URL"), #!!!
    (DISCORD, "Discord group URL"), #!!!
    (SLACK, "Slack group URL"), #!!!
  ]

  _contact_type_address= [
    (OTHER, "https://"),
    (EMAIL, "mailto:"),
    (PHONE, "tel:"),
    (WEBSITE, "https://"),
    (YOUTUBE, "https://www.youtube.com"),
    (TWITTER, "https://twitter.com"),
    (FACEBOOK, "https://www.facebook.com"),
    (INSTAGRAM, "https://www.instagram.com"),
    (LINKEDIN, "https://www.linkedin.com"), #!!!
    (VIMEO, "VIME"), #!!!
    (WHATSAPP, "https://chat.whatsapp.com"), #!!!
    (TELEGRAM, "https://t.me"), #!!!
    (DISCORD, "DCRD"), #!!!
    (SLACK, ".slack.com"), #!!!
  ]

  _contact_type_icon= [
    (OTHER, '/static/icon_globe.png'), #!
    (EMAIL, '/static/icon_mail.png'), #!
    (PHONE, '/static/icon_phone.png'), #!
    (WEBSITE, '/static/icon_globe.png'),
    (YOUTUBE, '/static/icon_yt30.png'), #!
    (TWITTER, '/static/icon_twitter30.png'),
    (FACEBOOK, '/static/icon_fb30.png'),
    (INSTAGRAM, '/static/icon_insta30.png'),
    (LINKEDIN, '/static/icon_linkedin.png'), #!
    (VIMEO, '/static/icon_vimeo.png'), #!
    (WHATSAPP, '/static/icon_whatsapp.png'), #!
    (TELEGRAM, '/static/icon_telegram.png'), #!
    (DISCORD, '/static/icon_discord.png'), #!
    (SLACK, '/static/icon_slack.png'), #!
  ]

  contacttype=models.CharField(max_length=4, choices=_contact_type_choices, default=OTHER)
  address=models.CharField(max_length=200, blank=False, null=False)
  info=models.CharField(max_length=200, blank=True, null=True)
  location = models.ForeignKey(Location, on_delete=models.CASCADE, blank=True, null=True)
  locationTitle=models.CharField(max_length=200, blank=True, null=True)
  category=models.CharField(max_length=200, blank=True, null=True)
  organization=models.ForeignKey(Organization, on_delete=models.CASCADE, blank=True, null=True)
  organizationTitle=models.CharField(max_length=200, blank=True, null=True)
  source=models.CharField(max_length=200, blank=True, null=True)

  '''
  ___descrition of self contacttype
  '''
  def description(self):
    for ctype in self._contact_type_choices:
      if ctype[0] == self.contacttype:
        return ctype[1]
  
  '''
  ___address of self contacttype
  '''
  def addressacces(self):
    for aatype in self._contact_type_address:
      if aatype[0] == self.contacttype:
        if (aatype[1] in self.address):
          return ""
        else:
          return aatype[1]
  
  '''
  ___icon of self contacttype
  '''
  def icon(self):
    for ctype in self._contact_type_icon:
      if ctype[0] == self.contacttype:
        return ctype[1]

  def url(self):
    link = self.address
    prefix = ''
    if self.contacttype == self.EMAIL:
      prefix = 'mailto:'
    elif self.contacttype == self.PHONE:
      prefix = 'tel:'
    else:
      prefix='https://'

    if not self.address.startswith(prefix):
      link = prefix+self.address

    return link
  
  def representative(self):
    return self.location==self.category

  '''
  ___
  '''
  def url(self):
    link = self.address
    prefix = ''
    if self.contacttype == self.EMAIL:
      prefix = 'mailto:'
    elif self.contacttype == self.PHONE:
      prefix = 'tel:'
    else:
      prefix='https://'

    if not self.address.startswith(prefix):
      link = prefix+self.address

    return link
  
  def representative(self):
    return self.location==self.category

  '''
  ___altered save function
  '''
  def save(self, *args, **kwargs):
    super(OrganizationContact, self).save(*args, **kwargs)
    if not self.location:
      self.location = Location.objects.filter(name__iexact=self.locationTitle).first() or Location.objects.get(id=Location.UNKNOWN)

    if self.location.id > Location.UNKNOWN:
      self.locationTitle = self.location.name
      self.category = self.location.in_country.name

    if not self.organization:
      self.organization=Organization.objects.filter(name__iexact=self.organizationTitle).first() or Organization.objects.get(id=Organization.UNKNOWN)

    if self.organization.id > Organization.UNKNOWN:
      self.organizationTitle = self.organization.name

    super(OrganizationContact, self).save(*args, **kwargs)

'''
???user data
'''
class UserHome(models.Model):
  def __str__(self):
    return self.callsign

  CALLSIGN = 'SIGN' # Just callsign
  PRIVATE  = 'PRIV' # + Country, State, Zip, Orgs
  FRIENDS  = 'FRND' # + Email to friends
  PUBLIC   = 'PUBL' # + Email to all
  OPENBOOK = 'OPEN' # + Phone, contact notes
  _visibility_level_choices = [
    (CALLSIGN, "Callsign only"), 
    (PRIVATE,  "Callsign, Country, State, Zip, Organizations"),
    (FRIENDS,  "Callsign, Country, State, Zip, Organizations, Closed Email (to friends and trusted organizations only)"), 
    (PUBLIC,   "Callsign, Country, State, Zip, Organizations, Open Email (to the world)"), 
    (OPENBOOK, "Callsign, Country, State, Zip, Organizations, Open Email, Phone and contact notes"),
  ]

  def get_visibility_str(self):
    return {key:val for (key, val) in UserHome._visibility_level_choices}[self.visibility_level]

  callsign = models.CharField(primary_key=True, max_length=25, unique=True)
  screenname = models.CharField(max_length=25, blank=True, null=True)
  #loginuser = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, editable=False)
  loginuser_id = models.IntegerField(blank=True, null=True)
  home_country = models.ForeignKey(Country, on_delete=models.PROTECT, blank=True, null=True)
  home_state = models.ForeignKey(Location, on_delete=models.PROTECT, blank=True, null=True)
  home_zip = models.CharField(max_length=12, blank=True, null=True)
  phone_number = models.CharField(max_length=25, blank=True, null=True)
  visibility_level = models.CharField(max_length=4, choices=_visibility_level_choices, default=CALLSIGN)
  contact_notes = models.CharField(max_length=200, blank=True, null=True)
  #organizations = models.ManyToManyField(Organization, blank=True)
  favorite_locations = models.ManyToManyField(Location, blank=True, related_name='favorite_of_user')
  recent_locations = models.ManyToManyField(Location, blank=True, related_name='recent_of_user')
  #verified = models.ForeignKey(Verification, on_delete=models.CASCADE, editable=False)
  #reputation
  #interests
  #friends

  UNKNOWN = 0
  def Unknown():
    if UserHome.objects.filter(id=Location.UNKNOWN).exists():
      return UserHome.objects.filter(id=Location.UNKNOWN).first()
    else:
      return None
  
  def SETUP_Unknown():
    if not UserHome.Unknown():
      unknown = UserHome()
      unknown.callsign = "User"
      unknown.loginuser_id = UserHome.UNKNOWN
      unknown.home_country = Country.Unknown()
      unknown.home_state = Location.Unknown()
      unknown.save()

  def SystemGenerate():
    if not UserHome.objects.filter(callsign="System").exists():
      uh = UserHome()
      uh.callsign = "System"
      uh.loginuser_id = 0
      uh.save()
      uh.home_country = Country.Unknown()
      uh.home_state = Location.Unknown()
      uh.save()

  def System():
    if not UserHome.objects.filter(callsign="System").exists():
      UserHome.SystemGenerate()
    return UserHome.objects.filter(callsign="System").first()

  

'''
???
'''
class Initiative(models.Model):
  def __str__(self):
    return self.name

  name = models.CharField(max_length=25)
  creation_date = models.DateTimeField(auto_now_add=True, editable=False)
  creator = models.ForeignKey(UserHome, related_name="initiatives_creator", on_delete=models.CASCADE, editable=False)
  description = models.CharField(max_length=2000)
  crew_users = models.ManyToManyField(UserHome, related_name="initiatives_crew", blank=True)
  interested_users = models.ManyToManyField(UserHome, related_name="initiatives_interest", blank=True)

'''
???
'''
class Action(models.Model):
  def __str__(self):
    return self.name

  name = models.CharField(max_length=25)
  registration_source = models.CharField(max_length=50, editable=False)
  creation_date = models.DateTimeField(auto_now_add=True, editable=False)
  creator = models.ForeignKey(UserHome, related_name="actions_creator", on_delete=models.SET_NULL, blank=True, null=True, editable=False)
  description = models.CharField(max_length=2000)
  crew_users = models.ManyToManyField(UserHome, related_name="actions_crew", blank=True)
  interested_users = models.ManyToManyField(UserHome, related_name="actions_interest", blank=True)
  action_link = models.URLField(max_length=500)

class Steward(models.Model):
  def __str__(self):
    return self.alias

  alias = models.CharField(max_length=100)

class Guide(Steward):
  ...

'''
___database cimate actions
'''
class Gathering(models.Model):
  def __str__(self):
    return self.regid

  STRIKE = 'STRK'
  DEMO = 'DEMO'
  NVDA = 'NVDA'
  MEETUP = 'MEET'
  OTHER = 'OTHR'
  CIRCLE = 'CIRC'
  _gathering_type_choices = [(STRIKE, "Strike"), (DEMO, "Demonstration"), 
    (NVDA, "Non-Violent Direct Action"), (MEETUP, "Meetup"), (CIRCLE, "Circle (MothersRebellion)"), (OTHER, "Other")]

  regid = models.CharField(primary_key=True, max_length=8, editable=False)
  gathering_type = models.CharField(max_length=4, choices=_gathering_type_choices, default=STRIKE)
  location = models.ForeignKey(Location, on_delete=models.SET_NULL, blank=False, null=True)
  start_date = models.DateField(blank=False,null=True)
  end_date = models.DateField(blank=True,null=True)
  duration = models.DurationField(blank=True, null=True)
  expected_participants = models.PositiveIntegerField(blank=True, null=True)
  organizations = models.ManyToManyField(Organization, blank=True)

  address = models.CharField(blank=True, max_length=64)
  time = models.CharField(blank=True, max_length=32)

  steward = models.ForeignKey(Steward, blank=True, null=True, on_delete=models.SET_NULL, related_name="steward_of_gathering")
  guide = models.ForeignKey(Guide, blank=True, null=True, on_delete=models.SET_NULL, related_name="guide_of_gathering")

  event_link_url = models.URLField(max_length=500, blank=True)
  contact_name = models.CharField(blank=True, max_length=256)
  contact_email = models.CharField(blank=True, max_length=256)
  contact_phone = models.CharField(blank=True, max_length=256)
  contact_notes = models.CharField(blank=True, max_length=256)

  @staticmethod
  def generate_regid():
    return ''.join([random.choice(string.ascii_letters+string.digits) for n in range(8)])

  '''
  ___Uniform table data
  '''
  def datalist_template(
      model = False, 
      date = False, 
      date_end = False, 
      activity_type = False, 
      overview = False, 
      gtype = False, 
      location = False, 
      country = False, 
      map_link = False, 
      orgs = False, 
      participants = False, 
      note_address = False, 
      note_time = False, 
      recorded = False, 
      event_link = False, 
      recorded_link = False, 
      record = False, 
      steward=False):
    return locals()
  
  def datalist(event, isrecord, datalist_template, green=None):
    values = {}
    obj_record = None
    obj_event = None
    if isrecord:
      obj_record = event
      obj_event = event.gathering
    else:
      obj_event = event
    
    try:
      key = 'date'
      if datalist_template[key]: 
        if isrecord: values[key] = date = obj_record.date 
        else: values[key] = date = obj_event.start_date
    except: pass
    try:
      key = 'date_end'
      if datalist_template[key]: values[key] = date_end = obj_event.end_date
    except: pass
    try:
      key = 'activity_type'
      if datalist_template[key]: 
        if isrecord: values[key] = activity_type = "Record"
        else: values[key] = activity_type = "Event"
    except: pass
    try:
      key = 'overview'
      if datalist_template[key]: values[key] = overview = obj_event.regid
    except: pass
    try:
      key = 'gtype'
      if datalist_template[key]: 
        for ch in Gathering.gathering_type.field.choices:
          if obj_event.gathering_type == ch[0]:
            values[key] = gtype = ch[1]
    except: pass
    try:
      key = 'location'
      if datalist_template[key]: values[key] = location = obj_event.location
    except: pass
    try:
      key = 'country'
      if datalist_template[key]: values[key] = country = obj_event.location.country_location()
    except: pass
    try:
      key = 'map_link'
      if datalist_template[key]: values[key] = map_link = "https://map.fridaysforfuture.org/?e="+obj_event.regid
    except: pass
    try:
      key = 'participants'
      if datalist_template[key]: 
        if isrecord: values[key] = participants = obj_record.participants
        else: values[key] = participants = obj_event.expected_participants
    except: pass
    try:
      key = 'orgs'
      if datalist_template[key]: 
        if isrecord: values[key] = orgs = obj_record.organization
        else: values[key] = orgs = obj_event.organizations.first()
    except: pass
    try:
      key = 'note_address'
      if datalist_template[key]: values[key] = note_address = obj_event.address
    except: pass
    try:
      key = 'note_time'
      if datalist_template[key]: values[key] = note_time = obj_event.time
    except: pass
    try:
      key = 'recorded'
      if datalist_template[key]: 
        if isrecord: values[key] = recorded = True
        else: values[key] = recorded = Gathering_Witness.objects.filter(gathering=obj_event.regid).exists()
    except: pass
    try:
      key = 'event_link'
      #print(f"ELO1 REC {isrecord} OBJ_EVENT {obj_event}")
      #if datalist_template[key]:
      #  print(f"ELO2 TMPL {datalist_template[key]}")
      #  print(f"ELO3 URL '{obj_event.event_link_url}'")
      if datalist_template[key]: values[key] = event_link = obj_event.event_link_url
      #print(f"ELO9 {obj_event}")
    except: pass
    try:
      key = 'recorded_link'
      if datalist_template[key]: values[key] = recorded_link = obj_record.proof_url
    except: pass
    try:
      key = 'steward'
      if datalist_template[key]: values[key] = steward = obj_event.steward
    except: pass
    
    if datalist_template['model']: values['model'] = model = event
    if datalist_template['record']: values['record'] = record = isrecord
    if green is not None: values['green'] = green

    #print(values)
    return values

  '''
  ___stringify self attributes
  '''
  def data_all(self):
    return "id:["+str(self.regid)+"]'"+str(self.gathering_type)+"', in "+str(self.location.name)+" date:["+str(self.start_date)+"->"+str(self.end_date)+"("+str(self.duration)+")]"+str(self.expected_participants)+" participants by "+str(self.organizations)+" place&time:["+str(self.address)+"&"+str(self.time)+"]"

  '''
  ___get type description from self gathering type
  '''
  def get_gathering_type_str(self):
    return {key:val for (key, val) in Gathering._gathering_type_choices}[self.gathering_type]

  '''
  ???calculate gathering type
  '''
  @staticmethod
  def get_gathering_type_code(s):
    for (key, val) in Gathering._gathering_type_choices:
      if s.casefold() == val.casefold():
        return key
    return Gathering.OTHER

  '''
  ???
  '''
  def get_canonical_regid(self):
    try:
      return Gathering_Belong.objects.get(regid=self.regid).gathering.regid
    except:
      return None
  
  '''
  ___stringify self location name
  '''
  def get_place_name(self):
    if not self.location:
      return "Unknown Place"
    return self.location.name


  '''
  ___stringigy self location parent name
  '''
  def get_in_location(self):
    if not self.location:
      return None
    return self.location.in_location

  '''
  ???find topgathering by following gathering belong
  '''
  def get_gathering_root(self):
    try:
      if hasattr(self, 'root_gathering'):
        return self.root_gathering
      self.root_gathering = Gathering_Belong.objects.get(regid=self.regid).gathering
      return self.root_gathering
    except:
      print(f"GXGB Gathering_Belong object not found for Gathering '{self.regid}'")
      return self

'''
???database object to remove duplicate gatherings
'''
class Gathering_Belong(models.Model):
  def __str__(self):
    return str(self.regid) + "=>" + str(self.gathering.regid)

  regid = models.CharField(primary_key=True, max_length=8, editable=False)
  gathering = models.ForeignKey(Gathering, on_delete=models.CASCADE)

  '''
  ???
  '''
  @classmethod
  def integrity_check():
    def detect_belongs_pointing_to_non_root_gatherings():
      bad_gbs=[]
      for gb in list(Gathering_Belong.objects.all()):
        if gb.gathering != Gathering_Belong.objects.filter(regid=gb.gathering).first().gathering:
          bad_gbs += [gb]
      print(f"ICGB {len(bad_gbs)} Gathering_Belong objects found that point to non-root Gatherings")
      for n, bgb in enumerate(bad_gbs,1):
        gat = bgb.regid
        for i in range(5): 
          bel = Gathering_Belong.objects.filter(regid=gat)
          print(f"ICGB {n}:{i}: {gat}/{Gathering.objects.filter(regid=gat).first().location} belongs {bel}")
          gat = bel.first().gathering
          if gat == Gathering_Belong.objects.filter(regid=gat).first().gathering:
            print(f"ICGB {n}:{i}: Rooted in {gat}/{Gathering.objects.filter(regid=gat).first().location}")
            print(f"""ICGB   Suggested fix: 
                             b=Gathering_Belong.objects.filter(regid="{bgb.regid}").first()
                             g=Gathering.objects.filter(regid="{gat}").first()
                             b.gathering=g
                             b.save()""")
            break
          siblings = Gathering_Belong.objects.filter(gathering=gat)
          print(f"ICGB   There are {len(siblings)} belongings pointing to this non root Gathering_Belong")
          for sn,sib in enumerate(siblings,1):
            print(f"ICGB {n}:{i}:{sn} {sib}")
      return bad_gbs

    return Gathering_Belong.detect_belongs_pointing_to_non_root_gatherings()

  '''
  ???
  '''
  def group_singleton_gatherings_by_loc(regid_list):
    # May be invoked manually by admin, not used by system
    for regid in regid_list:
      gat = models.Gathering.objects.filter(regid=regid).first()
      if not gat:
        print(f"Gat {regid} not found")
        continue
      loc = gat.location
      if not loc:
        print(f"Gat {regid} has no loc")
        continue
      cologat = None
      cologats = models.Gathering.objects.filter(location=loc)
      for colo in cologats:
        if colo.regid == regid:
          continue
        cologat = colo
        break
      if not cologat:
        print(f"Gat {gat} has no other gat at loc {loc}")
        continue
      print(f"Gat {gat} could be moved to gat {cologat}")
      bel = models.Gathering_Belong.objects.filter(regid=regid).first()
      if not bel:
        print(f"Gat {gat} has no Gathering_Belong")
        continue
      if bel.gathering.regid == colo.regid:
        print(f"Bel {regid} already moved to {colo.regid}")
        continue
      bel.gathering = colo
      bel.save()
      print(f"Bel {regid} moved to {colo.regid}")

'''
???database register of attending strike
'''
class Gathering_Witness(models.Model):
  def __str__(self):
    return str(self.gathering) + ":" + str(self.date)

  witness = models.ForeignKey(UserHome, on_delete=models.SET_NULL, blank=True, null=True, editable=False)
  gathering = models.ForeignKey(Gathering, on_delete=models.SET_NULL, null=True, editable=False)
  date = models.DateField()
  participants = models.PositiveIntegerField(blank=True, null=True, default=0)
  proof_url = models.URLField(max_length=500, blank=True)
  creation_time = models.DateTimeField(auto_now_add=True, editable=False)
  updated = models.DateTimeField(auto_now_add=True, null=True, editable=False)
  organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, blank=True, null=True, editable=False)
  steward = models.ForeignKey(Steward, blank=True, null=True, on_delete=models.SET_NULL, related_name="steward_of_gwitness")

  @staticmethod
  def get_witnesses(gathering, event_head):
    witnesses = []
    witnesses_here = list(Gathering_Witness.objects.filter(gathering=gathering))
    witness_by_date = {e.date:e for e in witnesses_here}
    the_date = gathering.start_date
    for w in witnesses_here:
      witnesses.append(Gathering.datalist(w, True, event_head, green=True))
    while the_date <= (gathering.end_date or gathering.start_date):
      if the_date not in witness_by_date.keys():
        record = Gathering.datalist(Gathering_Witness(
          gathering = gathering,
          date = the_date,
          participants = 0,
          proof_url = None,
          organization = gathering.organizations.first(),
        ), True, event_head, green=False)
        witnesses.append(record)
      the_date += datetime.timedelta(days=7)
    return witnesses

  '''
  ___parse map pin color by map strike type
  '''
  def get_pin_color(self):
    # FIXME: should be picked up from Coffer
    pin_color_map = {
      "blue": ["Weekly", "FridaysForFuture", "YFC blue", "Persistent Presence fridays For Future", "FFF Fridays For Future"],
      "dark red": ["Once / Irregular  month irregular dark red  year  yearly"],
      "grey": ["Historic  grey"],
      "yellow": ["11thHFC / Sunrise (prefer 11thHourForClimate) 11thHourForClimate  11thHour  yellow  11th Hour 11th Hour For The Climate 11thHFC Sunrise 11thhourforclimate"],
      "green": ["Online / EarthStrike / Digital / Training EarthStrike Earth Strike  green Online  digitalFFF  talksforfuture  training for future climatestrikeonline Fridays 4 Future Online FridaysforfutureOnline  Fridays4FutureOnline  Course  Training  training for future Digital DigitalFFF  Online strike"],
      "pink": ["Local / Work Group  Local Group pink  Work"],
      "black": ["Other (incl) XR / Ecocide  / WCUD/ RR / Ende Gelende /  Extinction Rebellion  XR  black By2020WeRiseUp  By2020  WorldCleanUpDay WCUD  WCD Other SOSAmazon Amazon  Buy nothing day Buynothingday Enköpfridag En köpfri dag Climate Roar  Ecocide Ende Gelende"],
      "dark blue": ["Parents / Family / Psychologists / Queers / AllFF AllForFuture  Zero Hour dark blue Earth Uprising  Psychologistsforfuture  psykologer  family for future physiotherapistsforfuture Queers4Climate  Parentsforfuture  föräldrar Parents for future  p4f Pff Grandparentsforfuture artistsforfuture  familyforfuture"],
      "red": ["ShoeProtest Shoestrike for future Shoestrikeforfuture red Shoestrikeff  Skostrejk Skostrejkff Skostrejkforfuture  ShoeProtest ShoeProtest for future  Shoe Strike ShoeStrike"],
      "orange": ["Teachers / Scientists / Researchers / Developers  ScientistsForFuture s4f orange  researchers desk  ResearchersDesk Teachersforfuture Teachers for future Teachers for climate  Teacherforclimate developersforfuture FridaysforfutureTeachers  Breaksforfuture"],
    }
    gat = self.gathering
    orgs = gat.organizations.all()
    for org in orgs:
      for col in pin_color_map:
        for name in pin_color_map[col]:
          #print(f"GPCN {self.date} {gat} org:{org} col:{col} mapname:'{name}' actname:'{org.name}'")
          if org.name.casefold() in name.casefold():
            return col
    return "black"

  '''
  ???
  '''
  def set_gathering_to_root(self):
    root_gathering = self.gathering.get_gathering_root()
    self.gathering.regid = root_gathering.regid
    return self.gathering.regid


'''
___
'''
class Verification(models.Model):
  created_by = models.ForeignKey(UserHome, on_delete=models.PROTECT, editable=False)
  created_on = models.TimeField(auto_now_add=True, editable=False)
  updated_on = models.TimeField(auto_now=True, editable=False)
  claim = models.FloatField(default=1, editable=False)
  strength = models.FloatField(default=0, editable=False)
  #notes = models.CharField(max_length=500)
  details = models.CharField(max_length=500)

  def defaultUser(details):
    v = Verification()
    v.created_by = UserHome.Unknown()
    v.created_on = datetime.datetime.now()
    v.updated_on = datetime.datetime.now()
    v.claim = 1
    v.strength = 0
    v.details = details
    v.save()

  def defaultSystem(details):
    v = Verification()
    v.created_by = UserHome.System()
    v.created_on = datetime.datetime.now()
    v.updated_on = datetime.datetime.now()
    v.claim = 10
    v.strength = 10
    v.details = details
    v.save()


'''
???google maps parsing
'''
class Gmaps_Locations(models.Model):
    place_id = models.CharField(max_length=30)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)

'''
???google maps parsing 
'''
class Gmaps_LookupString(models.Model):
    lookup_string = models.CharField(max_length=100)
    Gmaps_Location = models.ForeignKey(Gmaps_Locations, on_delete=models.CASCADE)


class PubKey(models.Model):
  def __str__(self):
    return f'<PubKey {self.pk}>'
  pubkey_str = models.CharField(max_length=80, editable=False)
  created_on = models.TimeField(auto_now_add=True, editable=False)
