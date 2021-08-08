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
from .static_lists import valid_location_ids
class Verification(models.Model):
  created_by = models.ForeignKey('UserHome', on_delete=models.PROTECT, editable=False)
  created_on = models.TimeField(auto_now_add=True, editable=False)
  updated_on = models.TimeField(auto_now=True, editable=False)
  claim = models.FloatField(default=1, editable=False)
  strength = models.FloatField(default=0, editable=False)

class Country(models.Model):
  def __str__(self):
    return self.name

  name = models.CharField(max_length=25)
  phone_prefix = models.CharField(max_length=5, blank=True)

  @staticmethod
  def as_set(static):
    return {country.name for country in Country.objects.all()}


class Location(models.Model):
  def __str__(self):
    return self.name

  name = models.CharField(max_length=100)
  #in_country = models.ForeignKey(Country, on_delete=models.PROTECT)
  in_location = models.ForeignKey('Location', on_delete=models.PROTECT, blank=True, null=True)
  zip_code = models.CharField(max_length=12, blank=True, null=True)
  lat = models.FloatField(blank=True, null=True)
  lon = models.FloatField(blank=True, null=True)
  #verified = models.ForeignKey(Verification, on_delete=models.CASCADE, editable=False)

  def country():
    toplocation = this
    for i in range(5):
      if toplocation.in_location:
        toplocation = in_location
      else:
        return toplocation

  @staticmethod
  def countries(generate = True):
    if generate:
      location_list = Location.objects.filter(lat__isnull=False)[:]
    else:
      location_list = Location.valid_ids(False)
    location_dict=dict()

    for location in location_list:
      country = location
      for x in range(5):
        if country.in_location:
          country = country.in_location
        else:
          break
      
      if country.name in location_dict:
        location_dict[country.name][2].append([location.name, location.id])
      else:
        location_dict.update({country.name:[country.name, country.id, list()]})
        location_dict[country.name][2].append([location.name, location.id])

    location_list = list(location_dict.values())
    
    return location_list

  @staticmethod
  def valid_ids(generate = False):
    generate = True
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

class Organization(models.Model):
  def __str__(self):
    return self.name

  name = models.CharField(max_length=50, unique=True)
  email = models.EmailField(blank=True)
  #verified = models.ForeignKey(Verification, on_delete=models.CASCADE, editable=False)

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

class Initiative(models.Model):
  def __str__(self):
    return self.name

  name = models.CharField(max_length=25)
  creation_date = models.DateTimeField(auto_now_add=True, editable=False)
  creator = models.ForeignKey(UserHome, related_name="initiatives_creator", on_delete=models.CASCADE, editable=False)
  description = models.CharField(max_length=2000)
  crew_users = models.ManyToManyField(UserHome, related_name="initiatives_crew", blank=True)
  interested_users = models.ManyToManyField(UserHome, related_name="initiatives_interest", blank=True)

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

class Gathering(models.Model):
  def __str__(self):
    return self.regid

  STRIKE = 'STRK'
  DEMO = 'DEMO'
  NVDA = 'NVDA'
  MEETUP = 'MEET'
  OTHER = 'OTHR'
  _gathering_type_choices = [(STRIKE, "Strike"), (DEMO, "Demonstration"), 
    (NVDA, "Non-Violent Direct Action"), (MEETUP, "Meetup"), (OTHER, "Other")]

  regid = models.CharField(primary_key=True, max_length=8, editable=False)
  gathering_type = models.CharField(max_length=4, choices=_gathering_type_choices, default=STRIKE)
  location = models.ForeignKey(Location, on_delete=models.SET_NULL, blank=True, null=True)
  start_date = models.DateField(blank=True,null=True)
  end_date = models.DateField(blank=True,null=True)
  duration = models.DurationField(blank=True, null=True)
  expected_participants = models.PositiveIntegerField(blank=True, null=True)
  organizations = models.ManyToManyField(Organization, blank=True)

  address = models.CharField(blank=True, max_length=64)
  time = models.CharField(blank=True, max_length=32)

  contact_name = models.CharField(blank=True, max_length=64)
  contact_email = models.CharField(blank=True, max_length=64)
  contact_phone = models.CharField(blank=True, max_length=64)
  contact_notes = models.CharField(blank=True, max_length=64)

  def get_gathering_type_str(self):
    return {key:val for (key, val) in Gathering._gathering_type_choices}[self.gathering_type]

  @staticmethod
  def get_gathering_type_code(s):
    for (key, val) in Gathering._gathering_type_choices:
      if s.casefold() == val.casefold():
        return key
    return Gathering.OTHER

  def get_canonical_regid(self):
    try:
      return Gathering_Belong.objects.get(regid=self.regid).gathering.regid
    except:
      return None
  
  def get_place_name(self):
    if not self.location:
      return "Unknown Place"
    return self.location.name

  def get_in_location(self):
    if not self.location:
      return None
    return self.location.in_location

class Gathering_Belong(models.Model):
  def __str__(self):
    return str(self.regid) + "=>" + str(self.gathering.regid)

  regid = models.CharField(primary_key=True, max_length=8, editable=False)
  gathering = models.ForeignKey(Gathering, on_delete=models.CASCADE)

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
