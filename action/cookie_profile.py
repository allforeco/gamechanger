from django.template import loader
from django.http import HttpResponse
from django.shortcuts import redirect
from django.forms import *
#from django.forms import UploadFileForm

from io import StringIO
from dal import autocomplete
import csv

from .models import Gathering, Organization, OrganizationContact, Location, Country

def loginCookieProfile(request):
  profile_dict = {}
  export = []
  profile_user_dict = {}

  profile_active = CookieProfile.get_value(request, CookieProfile.COOKIE_PROFILE)
  if (profile_active):
    profile_dict = CookieProfile.get_values(request)
    export = CookieProfile.exportprofile(request)
    profile_user_dict = {}
    key = CookieProfile.ALIAS
    if profile_dict[key]:
      profile_user_dict[key] = profile_dict[key]
    key = CookieProfile.EMAIL
    if profile_dict[key]:
      profile_user_dict[key] = profile_dict[key]
    key = CookieProfile.ORGANIZATION
    if profile_dict[key] != -1:
      profile_user_dict[key] = Organization.objects.get(id=profile_dict[key])
    key = CookieProfile.COUNTRY
    if profile_dict[key] != -1:
      profile_user_dict[key] = Country.objects.get(id=profile_dict[key])
    key = CookieProfile.LOCATION
    if profile_dict[key] != -1:
      profile_user_dict[key] = Location.objects.get(id=profile_dict[key])

  template = loader.get_template('action/cookie_profile.html')
  context = {
    'export': export,
    'profile_active': CookieProfile.get_value(request, CookieProfile.COOKIE_PROFILE),
    'profile_dict': profile_dict,
    'profile_user_dict': profile_user_dict,
    'form': CookieProfile.profile_form(),
  }

  return HttpResponse(template.render(context, request))

'''
___
'''
class CookieProfile():
  COOKIE_PROFILE = 'cookie_profile'
  USER_CONSENT = 'user_consent'
  ALIAS = 'alias'
  EMAIL = 'email'
  PHONE = 'phone'
  CONATCT_NOTES = 'contact_notes'
  SPOKEPERSON_CONSENT = 'spokeperson_consent'
  ORGANIZATION = 'organization'
  COUNTRY = 'country'
  LOCATION = 'town'

  keys = [
    COOKIE_PROFILE,
    USER_CONSENT,
    ALIAS,
    EMAIL,
    PHONE,
    CONATCT_NOTES,
    SPOKEPERSON_CONSENT,
    ORGANIZATION,
    COUNTRY,
    LOCATION,
  ]

  def get_values(request):
    values = {}
    if CookieProfile.COOKIE_PROFILE not in request.session:
      request.session[CookieProfile.COOKIE_PROFILE] = False

    if request.session[CookieProfile.COOKIE_PROFILE]:
      for key in CookieProfile.keys:
        values[key] = request.session[key]
      return values
    else:
      values[CookieProfile.COOKIE_PROFILE] = False
      return values
    
  def get_value(request, key):
    if key in request.session:
      return request.session[key]
    
    return None
  
  def logout(request):
    request.session[CookieProfile.COOKIE_PROFILE] = False
    return redirect('action:login_cookie_profile')

  def importprofile(request):
    #data = request.POST
    files = request.FILES

    import_file = files['import']
    datar = import_file.read().decode(encoding='UTF-8')

    datac = csv.reader(datar.splitlines())
    data = list()
    for row in datac:
      data.append(row)

    i=0
    for key in data[0]:
      if key in CookieProfile.keys:
        request.session[key] = data[1][i]
        print(key, data[1][i])
      i+=1
          
    return redirect('action:login_cookie_profile')
  
  def exportprofile(request):
    if not request.session[CookieProfile.COOKIE_PROFILE]:
      return
    
    text = ""
    filename = f"gamechanger_cookie_profile ({request.session[CookieProfile.ALIAS]}{request.session[CookieProfile.ORGANIZATION]}{request.session[CookieProfile.COUNTRY]}).gcp"

    for key in CookieProfile.keys:
      text += f"{key},"
    text += str(chr(10))
    for key in CookieProfile.keys:
      text += f"{request.session[key]},"

    return (filename, text)

  
  def createprofile(request):
    data = request.POST
    print(data)

    for item in data:
      if item in CookieProfile.keys:
        print(item, data[item])
        request.session[item] = data[item]

    if not request.session[CookieProfile.ORGANIZATION].isnumeric():
      request.session[CookieProfile.ORGANIZATION] = -1

    if not request.session[CookieProfile.COUNTRY].isnumeric():
      request.session[CookieProfile.COUNTRY] = -1

    if not request.session[CookieProfile.LOCATION].isnumeric():
      request.session[CookieProfile.LOCATION] = -1

    if data[CookieProfile.USER_CONSENT] == 1:
      print("CPCP","send to FFF")

    return redirect('action:login_cookie_profile')

  class profile_form(Form):
    CONSENT_NO=0
    CONSENT_YES=1
    _consent_options=[
      (CONSENT_NO, "NO: I do not agree that (FFF) store my personal information."),
      (CONSENT_YES, "YES: I agree that (FFF) store my personal information (until I tell FFF to remove it). We (FFF) will use the information to potentialy get in touch with you."),
    ]
    user_consent = ChoiceField(label="Share with FFF",choices=_consent_options, required=True)
    user_consent.widget.attrs.update({"onchange": "consent_requirement()", "class":"dropdown select2-selection select2-selection--single"})
    
    SPOKEPERSON_PRIVATE=0
    SPOKEPERSON_MEDIA=1
    SPOKEPERSON_PUBLIC=2
    _spokeperson_options = [
      (SPOKEPERSON_PRIVATE, "Private: No, I do not wish my registration identity (name, email, phone) to be known to people outside FFF."),
      (SPOKEPERSON_MEDIA, "Media: Yes, I volunteer to be a media spokesperson. I agree that my contact information (name, email, phone, country, city, notes) may be given to media representatives."),
      (SPOKEPERSON_PUBLIC, "Public: Yes, I volunteer to be a public organizer and spokesperson. Share my contact details (name, email, phone, country, city, notes) on the web, on maps, in social media, traditional media, etc.")
    ]
    spokeperson_consent=ChoiceField(label="Organization Spokesperson",choices=_spokeperson_options)
    spokeperson_consent.widget.attrs.update({"onchange": "consent_requirement()", "class":"dropdown select2-selection select2-selection--single"})

    alias = CharField(label="Name/Alias")
    email = EmailField(label="Email")
    phone=CharField(label="Phone#")
    contact_notes=CharField(label="Contact Notes")

    organization = ModelChoiceField(label="Organization", widget=autocomplete.ModelSelect2(url='/action/organization-autocomplete/'), queryset=Organization.objects.all().order_by('name'))
    
    country = ModelChoiceField(label="Country", widget=autocomplete.ModelSelect2(url='/action/country-autocomplete/'), queryset=Country.objects.all().order_by('name'))
    town = ModelChoiceField(label="Location", widget=autocomplete.ModelSelect2(url='/action/location-incountry-filter/', forward=['country']), queryset=Location.objects.exclude(in_country=Country.Unknown()).order_by('name'))
