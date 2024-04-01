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
import pycountry

'''
___
'''
class Verification(models.Model):
  created_by = models.ForeignKey('UserHome', on_delete=models.PROTECT, editable=False)
  created_on = models.TimeField(auto_now_add=True, editable=False)
  updated_on = models.TimeField(auto_now=True, editable=False)
  claim = models.FloatField(default=1, editable=False)
  strength = models.FloatField(default=0, editable=False)

'''
___Database registered Locations
'''
class Location(models.Model):
  def __str__(self):
    return f"{self.name}, {self.in_country.code}"

  name = models.CharField(max_length=100)
  in_country = models.ForeignKey('Country', on_delete=models.CASCADE, blank=True, null=True)
  in_location = models.ForeignKey('Location', on_delete=models.PROTECT, blank=True, null=True)
  zip_code = models.CharField(max_length=12, blank=True, null=True)
  lat = models.FloatField(blank=True, null=True)
  lon = models.FloatField(blank=True, null=True)
  #google_name = models.CharField(max_length=255, null=True, blank=True)
  verified = models.ForeignKey(Verification, on_delete=models.CASCADE, blank=True, null=True)
  google_metadata = models.CharField(max_length=1023,blank=True, null=True)

  '''
  ___stringify coordinates
  '''
  def str_lat_lon(self):
    return f"({self.lat},{self.lon})"

  '''
  ___location integrity by
  ___country and coordinate validity
  '''
  def tracable(self):
    t=0
    if self.in_country != Country.objects.get(id=-1): t+=1
    if self.lat != None and self.lon != None: t+=1
    return t
  
  def Unknown():
    return Location.objects.get(id=-1)
  
  '''
  ___location search
  ___order by name start->contains, searchterm q
  ___option include/exclude unknown country
  '''
  def search(q, option = 0):
    if option == 1:
      ls = Location.objects.all()
    else:
      ls = Location.objects.exclude(in_country=Country.Unknown())
    ls = ls.filter(name__icontains=q)
    lout = ls.filter(name__istartswith=q)
    lout |= ls.exclude(name__istartswith=q)
    return lout
  
  '''
  ___Get location of country
  '''
  def country_location(self):
    locations = Location.objects.filter(in_country=self.in_country, name=self.in_country.name)
    if locations.count() > 0:
      return locations.first()
    else:
      return Location.Unknown()
  
  '''
  ___finds toplocation as country
  '''
  def country(self):
    toplocation = self
    for i in range(5):
      if toplocation.in_location:
        toplocation = toplocation.in_location
      else:
        return toplocation

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
  
  def Unknown():
    return Country.objects.get(id=-1)
  
  '''
  ___Get location of country
  '''
  def country_location(self):
    locations = Location.objects.filter(in_country=self, name=self.name)
    if locations.count() > 0:
      return locations.first()
    else:
      return Location.Unknown()

  '''
  ___organization search
  ___order by name start->contains, searchterm q
  ___option include/exclude unknown country
  '''
  def search(q, option = 0):
    if option == 1:
      csr = Country.objects.all()
    else:
      csr = Country.objects.exclude(id=-1)
    cs = csr.filter(code__iexact=q)
    cs |= csr.filter(name__icontains=q)

    cout = cs.filter(code__iexact=q)
    cout |= cs.filter(name__istartswith=q)
    cout |= cs.exclude(name__istartswith=q)
    return cout

  '''
  ___pycountry lookup
  '''
  def pycy_lookup(name):
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
        pycy = pycountry.countries.search_fuzzy(name)[0]
      
      if Country.objects.filter(name=pycy.name).exists():
        return Country.objects.get(name=pycy.name)
      else:
        return Country.Unknown()
    except:
      return Country.Unknown()

  '''
  ___generate countries
  ___by location country calculation matching pycountry
  '''
  def generate(option = 0):
    if option == 1:
      Country.objects.all().delete()

    c = Country()
    c.id = -1
    c.name = "Unknown"
    c.code = "XX"
    c.flag = "🏳️"
    c.save()

    for location in Location.objects.all():
      
      l = location.country()
      pycy=Country.pycy_lookup(l.name)
      if pycy == Country.Unknown():
        location.in_country=Country.Unknown()
        location.save()
        continue

      #try:
      #  if pycountry.countries.get(alpha_2=l.name):
      #    pycy = pycountry.countries.get(alpha_2=l.name)
      #  elif pycountry.countries.get(alpha_3=l.name):
      #    pycy = pycountry.countries.get(alpha_3=l.name)
      #  elif pycountry.countries.get(name=l.name):
      #    pycy = pycountry.countries.get(name=l.name)
      #  elif pycountry.countries.get(official_name=l.name):
      #    pycy = pycountry.countries.get(official_name=l.name)
      #  elif pycountry.countries.search_fuzzy(l.name):
      #    pycy = pycountry.countries.search_fuzzy(l.name)[0]
      #  else:
      #    location.in_country=Country.Unknown()
      #    location.save()
      #    continue
      #except:
      #  location.in_country=Country.Unknown()
      #  location.save()
      #  #print("failed", l.name)
      #  continue

      if not Country.objects.filter(name=pycy.name).exists():
        #print(l.name)
        name = pycy.name
        loc = l
        code = pycy.alpha_2
        flag = pycy.flag
        #print(name, location, code, flag, pycy, "\n")
        c = Country()
        c.name = name
        #c.location = location
        c.code = code
        c.flag = flag
        c.save()
        location.in_country = Country.objects.get(name=pycy.name)
        location.save()
      else:
        location.in_country = Country.objects.get(name=pycy.name)
        location.save()

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
      os = Organization.objects.exclude(id=-1)
    os = os.filter(name__icontains=q)
    oout = os.filter(name__istartswith=q)
    oout |= os.exclude(name__istartswith=q)
    return oout
  
  def Unknown():
    return Organization.objects.get(id=-1)

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
      self.location = Location.objects.filter(name__iexact=self.locationTitle).first() or Location.objects.get(id=-1)

    if self.location.id > -1:
      self.locationTitle = self.location.name
      self.category = self.location.country().name

    if not self.organization:
      self.organization=Organization.objects.filter(name__iexact=self.organizationTitle).first() or Organization.objects.get(id=-1)

    if self.organization.id > -1:
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

  callsign = models.CharField(primary_key=True, max_length=25)
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

  def Unknown():
    return UserHome.objects.filter(callsign="User").first()

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

'''
___database cimate actions
'''
class Gathering(models.Model):
  def __str__(self):
    return str(self.regid)+":"+str(self.location.name)+"-"+str(self.start_date)

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

  #event_link_url = models.URLField(max_length=500, blank=True)
  contact_name = models.CharField(blank=True, max_length=64)
  contact_email = models.CharField(blank=True, max_length=64)
  contact_phone = models.CharField(blank=True, max_length=64)
  contact_notes = models.CharField(blank=True, max_length=64)

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

  
