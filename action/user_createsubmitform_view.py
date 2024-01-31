from django.template import loader
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django import forms

from dal import autocomplete
import base64, hashlib, datetime

from .models import Gathering, Organization, OrganizationContact, Location

'''
___formclass for gathering
'''
class GatheringCreateForm(forms.ModelForm):
  consent = forms.BooleanField()
  class Meta():
    model = Gathering
    fields = ['gathering_type', 'location', 'start_date', 'duration', 'expected_participants', 'time', 'address']
    widgets = {
      'location': autocomplete.ModelSelect2(url='/action/location-autocomplete/'),
      'start_date': forms.DateInput(attrs={'type': 'date', 'value':'yyyy-mm-dd'}),
      'duration': forms.NumberInput(attrs={'min': '0'}),
    }

'''
___view for contact form
'''
def GatheringCreateSubmit(request):
  logginbypass = False
  if not (request.user.is_authenticated or logginbypass): return redirect('action:start')

  template = loader.get_template('action/form_CreateSubmit.html')
  context = {'form': GatheringCreateForm(), 'createsubmit_title': "Event", 'formaction_url': "create_gathering"}
  return HttpResponse(template.render(context, request))

'''
___create gathering by form data
___redirect loop
'''
def GatheringCreate(request):
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
class OrganizationCreateForm(forms.ModelForm):
  class Meta():
    model = Organization
    fields = ['name']

'''
___organization form view
'''
def OrganizationCreateSubmit(request):
  logginbypass = False
  if not (request.user.is_authenticated or logginbypass): return redirect('action:start')
  template = loader.get_template('action/form_CreateSubmit.html')
  context = {'form': OrganizationCreateForm(), 'createsubmit_title': "Organization", 'formaction_url': "create_organization"}
  return HttpResponse(template.render(context, request))

'''
___Organization create by form
___contact redirect
'''
def OrganizationCreate(request):
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
class OrganizationcontactCreateForm(forms.ModelForm):
  class Meta():
    model = OrganizationContact
    fields = ['contacttype', 'address', 'info', 'organization', 'location']

'''
___form view for contact
'''
def OrganizationcontactCreateSubmit(request):
  logginbypass = False
  if not (request.user.is_authenticated or logginbypass): return redirect('action:start')
  template = loader.get_template('action/form_CreateSubmit.html')
  context = {'form': OrganizationcontactCreateForm(), 'createsubmit_title': "Organization Contact", 'formaction_url': "create_organizationcontact"}
  return HttpResponse(template.render(context, request))

'''
___create contact by form data
___redirect loop
'''
def OrganizationcontactCreate(request):
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

