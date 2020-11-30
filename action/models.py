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

class Location(models.Model):
  def __str__(self):
    return self.name

  name = models.CharField(max_length=100)
  #in_country = models.ForeignKey(Country, on_delete=models.PROTECT)
  in_location = models.ForeignKey('Location', on_delete=models.PROTECT, blank=True, null=True)
  zip_code = models.CharField(max_length=12, blank=True)
  lat = models.FloatField(blank=True, null=True)
  lon = models.FloatField(blank=True, null=True)
  #verified = models.ForeignKey(Verification, on_delete=models.CASCADE, editable=False)

class Organization(models.Model):
  def __str__(self):
    return self.name

  name = models.CharField(max_length=25, unique=True)
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
    (CALLSIGN, "Only callsign"), 
    (PRIVATE,  "+ Country, State, Zip, Organizations"),
    (FRIENDS,  "+ Email (to friends and trusted organizations)"), 
    (PUBLIC,   "+ Email (to the world)"), 
    (OPENBOOK, "+ Phone and contact notes")
  ]

  callsign = models.CharField(primary_key=True, max_length=25)
  screenname = models.CharField(max_length=25, blank=True, null=True)
  loginuser = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, editable=False)
  home_country = models.ForeignKey(Country, on_delete=models.PROTECT, blank=True, null=True)
  home_state = models.ForeignKey(Location, on_delete=models.PROTECT, blank=True, null=True)
  home_zip = models.CharField(max_length=12, blank=True, null=True)
  phone_number = models.CharField(max_length=25, blank=True, null=True)
  visibility_level = models.CharField(max_length=4, choices=_visibility_level_choices, default=CALLSIGN)
  contact_notes = models.CharField(max_length=200, blank=True, null=True)
  organizations = models.ManyToManyField(Organization, blank=True, null=True)
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
  action_link = models.URLField(max_length=200)

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
  expected_participants = models.IntegerField(blank=True, null=True)

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
  participants = models.IntegerField(blank=True, null=True, default=0)
  proof_url = models.URLField(max_length=200, blank=True)
  creation_time = models.DateTimeField(auto_now_add=True, editable=False)
  updated = models.DateTimeField(auto_now_add=True, null=True, editable=False)
