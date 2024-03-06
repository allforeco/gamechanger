from django.template import loader
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.forms import *
from .bigredbutton import BigRedButton

from dal import autocomplete
import base64, hashlib, datetime

from .models import Gathering, Organization, OrganizationContact, Location, Country

publicuse = True



'''
___formclass gathering
'''
class GatheringCreateForm(ModelForm):
  class Meta():
    model = Gathering
    fields = ['gathering_type', 'location', 'start_date', 'duration', 'expected_participants', 'time', 'address']
    widgets = {
      'location': autocomplete.ModelSelect2(url='/action/location-autocomplete/'),
      'start_date': DateInput(attrs={'type': 'date', 'value':'yyyy-mm-dd'}),
      'duration': NumberInput(attrs={'min': '0'}),
    }
'''
___view for contact form
'''
def GatheringCreateSubmit(request):
  logginbypass = publicuse
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:premission_denied')

  template = loader.get_template('action/form_CreateSubmit.html')
  context = {'form': GatheringCreateForm(), 'createsubmit_title': "Event", 'formaction_url': "create_gathering"}
  return HttpResponse(template.render(context, request))

'''
___create gathering by form data
___redirect loop
'''
def GatheringCreate(request):
  logginbypass = publicuse
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:premission_denied')
  data = request.POST

  try:
    regid = base64.urlsafe_b64encode(hashlib.md5(str(data['gathering_type']+":"+data['location']+":"+data['start_date']).encode()).digest()).decode()[:8]
    gathering_type = data['gathering_type']
    location = Location.objects.get(id=data['location']) or Location.objects.get(id=-1)
    start_date = datetime.datetime.strptime(data['start_date'], "%Y-%m-%d")
    duration = datetime.timedelta(weeks=int(data['duration']))
    end_date =  start_date+duration
    expected_participants = data['expected_participants']
    #organizations.add(Organization.objects.get(id=-1))#data['organizations'] or 
    address = data['address']
    time = data['time']
    consent = data['consent']
  except:
    return redirect('action:gathering_submit')
  
  if consent == False:
    return redirect('action:gathering_submit')
  
  gathering = Gathering()
  gathering.regid = regid #= models.CharField(primary_key=True, max_length=8, editable=False)
  gathering.gathering_type = gathering_type #= models.CharField(max_length=4, choices=_gathering_type_choices, default=STRIKE)
  gathering.location = location #= models.ForeignKey(Location, on_delete=models.SET_NULL, blank=True, null=True)
  gathering.start_date = start_date #= models.DateField(blank=True,null=True)
  gathering.duration = duration #= models.DurationField(blank=True, null=True)
  gathering.end_date = end_date #= models.DateField(blank=True,null=True)
  gathering.expected_participants = expected_participants #= models.PositiveIntegerField(blank=True, null=True)
  #gathering.organizations.add(Organization.objects.get(id=-1))#data['organizations'] or  #= models.ManyToManyField(Organization, blank=True)
  gathering.address = address #= models.CharField(blank=True, max_length=64)
  gathering.time = time #= models.CharField(blank=True, max_length=32)
  gathering.save()

  print(gathering.data_all())
  return redirect('action:gathering_submit')


  
'''
___organization formclass
'''
class OrganizationCreateForm(ModelForm):
  class Meta():
    model = Organization
    fields = ['name']

'''
___organization form view
'''
def OrganizationCreateSubmit(request):
  logginbypass = publicuse
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:premission_denied')
  template = loader.get_template('action/form_CreateSubmit.html')
  context = {'form': OrganizationCreateForm(), 'createsubmit_title': "Organization", 'formaction_url': "create_organization"}
  return HttpResponse(template.render(context, request))

'''
___Organization create by form
___contact redirect
'''
def OrganizationCreate(request):
  logginbypass = publicuse
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:premission_denied')
  data = request.POST
  print(data)

  try:
    name = data['name']
  except:
    redirect('action:organization_submit')

  organization = Organization()
  organization.name = name
  organization.verified = False
  organization.save()
  return redirect('action:organizationcontact_submit')

'''
___formclass for contact
'''
class OrganizationcontactCreateForm(ModelForm):
  class Meta():
    model = OrganizationContact
    fields = ['contacttype', 'address', 'info', 'organization', 'location']

'''
___form view for contact
'''
def OrganizationcontactCreateSubmit(request):
  logginbypass = publicuse
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:premission_denied')
  template = loader.get_template('action/form_CreateSubmit.html')
  context = {'form': OrganizationcontactCreateForm(), 'createsubmit_title': "Organization Contact", 'formaction_url': "create_organizationcontact"}
  return HttpResponse(template.render(context, request))

'''
___create contact by form data
___redirect loop
'''
def OrganizationcontactCreate(request):
  logginbypass = publicuse
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:premission_denied')
  data = request.POST
  print(data)

  try:
    contacttype= data['contacttype']
    address=data['address']
    info=data['info']
    organization=Organization.objects.get(id=data['organization'])
    location=Location.objects.get(id=data['location'])
  except:
    return redirect('action:organizationcontact_submit')
  
  organizationcontact = OrganizationContact()
  organizationcontact.contacttype = contacttype
  organizationcontact.address = address
  organizationcontact.info = info
  organizationcontact.organization=organization
  organizationcontact.location=location
  organizationcontact.save()

  return redirect('action:organizationcontact_submit')


'''
___formclass location
'''
class LocationParseForm(Form):
  country = CharField(required=True)
  state = CharField()
  county = CharField()
  town = CharField()
  address = CharField()
  #lat = FloatField()
  #lon = FloatField()

def LocationCreateSubmit(request):
  publicuse = False
  logginbypass = publicuse
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:premission_denied')
  template = loader.get_template('action/form_CreateSubmit.html')
  context = {'form': LocationParseForm(), 'createsubmit_title': "Location", 'formaction_url': "create_location"}
  return HttpResponse(template.render(context, request))

def LocationCreate(request):
  publicuse = False
  logginbypass = publicuse
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:premission_denied')
  data = request.POST
  print(data)

  input_address = ",".join([data['address'], data['town'], data['county'], data['state'], data['country']])
  input_latlon = data['lat'] + "," + data['lon']
  return redirect('action:location_submit')

'''REPLACED BY COOKIE_PROFILE
___formclass for userspokegathering
'''
#class UserSpokeGathering(Form):
class USGformuser(Form):
  CONSENT_NO=0
  CONSENT_YES=1
  _consent_options=[
    (CONSENT_NO, "NO: I do not wish to have my email and alias stored."),
    (CONSENT_YES, "YES: I agree that (FFF) store my personal information (until I tell FFF to remove it). We will use the information to potentialy get in touch with you."),
  ]
  user_consent = ChoiceField(choices = _consent_options, label="Registration Consent",help_text=f"{_consent_options[CONSENT_NO][1]} <br/> {_consent_options[CONSENT_YES][1]}" , required=True)

  user_email = EmailField(label="Email")
  user_alias = CharField(label="Name/Alias")

class USGformspokeperson(Form):
  SPOKEPERSON_PRIVATE=0
  SPOKEPERSON_MEDIA=1
  SPOKEPERSON_PUBLIC=2
  _spokeperson_options = [
    (SPOKEPERSON_PRIVATE, "Private: No, I do not wish my registration identity (name, email, phone) to be known to people outside FFF."),
    (SPOKEPERSON_MEDIA, "Media: Yes, I volunteer to be a media spokesperson. I agree that my contact information (name, email, phone, country, city, notes) may be given to media representatives."),
    (SPOKEPERSON_PUBLIC, "Public: Yes, I volunteer to be a public organizer and spokesperson. Share my contact details (name, email, phone, country, city, notes) on the web, on maps, in social media, traditional media, etc.")
  ]
  spokeperson_consent=ChoiceField(choices=_spokeperson_options,help_text=f"{_spokeperson_options[SPOKEPERSON_PRIVATE][1]}<br/>{_spokeperson_options[SPOKEPERSON_MEDIA][1]}<br/>{_spokeperson_options[SPOKEPERSON_PUBLIC][1]}")
  spokeperson_organizations = ModelChoiceField(queryset=Organization.objects.all().order_by('name'))
  spokeperson_phone=CharField()
  spokeperson_notes=CharField()

class USGformgathering(Form):
  CONSENT_PRIVATE = 0
  CONSENT_PUBLIC = 1
  _consent_options=[
    (CONSENT_PRIVATE, "Private Gathering"),
    (CONSENT_PUBLIC, "Public Gathering")
  ]
  gathering_consent = ChoiceField(choices=_consent_options)
  gathering_type = ChoiceField(choices=Gathering._gathering_type_choices)
  gathering_country = ModelChoiceField(widget=autocomplete.ModelSelect2(url='/action/country-autocomplete/'), queryset=Country.objects.all().order_by('name'))
  gathering_location = ModelChoiceField(widget=autocomplete.ModelSelect2(url='/action/location-incountry-filter/', forward=['gathering_country']), queryset=Location.objects.exclude(in_country=Country.Unknown()).order_by('name'))
  #ModelChoiceField(queryset=Location.objects.exclude(in_country=Country.Unknown()).order_by('name', 'in_country')) #
  gathering_address = CharField()
  gathering_link = CharField()
  gathering_link_success = CharField()

  FREQUENCY_ONCE=0
  FREQUENCY_YEAR=1
  FREQUENCY_MONTH=2
  FREQUENCY_WEEKLY=3
  FREQUENCY_DAY=4
  _frequency_choices = [
    (FREQUENCY_ONCE, "Once"),
    (FREQUENCY_YEAR, "Yearly"),
    (FREQUENCY_MONTH, "Monthly"),
    (FREQUENCY_WEEKLY, "Weekly"),
    (FREQUENCY_DAY, "Daily")
  ]
  gathering_frequency = ChoiceField(choices=_frequency_choices)
  gathering_start_date = DateField()
  gathering_duration = DurationField()
  gathering_expected_participants = IntegerField(min_value=0)

  #def __init__(self, *args, **kwargs):
  #  super(USGformgathering, self).__init__(*args, **kwargs)
  #  cc = Country.Unknown()
  #  print("cc", cc)
  #  self.fields['country'].clean(cc)
  #  self.fields['location'].queryset = Location.objects.filter(in_country=cc)


def USGCreateSubmit(request):
  logginbypass = publicuse
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:premission_denied')

  template = loader.get_template('action/form_USG_CreateSubmit.html')
  context = {
    'form_user': USGformuser(), 
    'form_spokeperson': USGformspokeperson(), 
    'form_gathering': USGformgathering()
    }
  return HttpResponse(template.render(context, request))

def USGCreate(request):
  logginbypass = publicuse
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:premission_denied')
  data = request.POST
  try:
    user_consent = data['user_consent']
    user_email = data['user_email'] #EmailField(label="Email")
    user_alias = data['user_alias'] #CharField(label="Name/Alias")
  except:
    "continue"

  try:
    spokeperson_consent = data['spokeperson_consent']
    spokeperson_organizations = data['spokeperson_organizations'] #ModelChoiceField(queryset=Organization.objects.all().order_by('name'))
    spokeperson_phone = data['spokeperson_phone'] #CharField()
    spokeperson_notes = data['spokeperson_notes'] #CharField()
  except:
    "continue"

  try:
    gathering_consent = data['gathering_consent']
    gathering_type = data['gathering_type'] #ChoiceField(choices=Gathering._gathering_type_choices)
    gathering_country = data['gathering_country'] #ModelChoiceField(queryset=Country.objects.all().order_by('name'), widget=Select(attrs={'onchange':'Submit()'}))
    gathering_location = data['gathering_location'] #ModelChoiceField(queryset=Location.objects.exclude(in_country=Country.Unknown()).order_by('name', 'in_country'))
    gathering_address = data['gathering_address'] #CharField()
    gathering_link = data['gathering_link'] #CharField()
    gathering_link_success = data['gathering_link_success'] #CharField()
    gathering_frequency = data['gathering_frequency'] #ChoiceField(choices=_frequency_choices)
    gathering_start_date = data['gathering_start_date'] #DateField()
    gathering_duration = data['gathering_duration'] #DurationField()
    gathering_expected_participants = data['gathering_expected_participants'] #IntegerField(min_value=0)  
  except:
    "continue"

  return redirect('action:start')