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

  export = CookieProfile.exportprofile(request)

  #form_import = UploadFileForm(request.POST, request.FILES)

  template = loader.get_template('action/cookie_profile.html')
  context = {
    'export_filename': export[0],
    'export_text': export[1],
    #'form_import': form_import,
    'profile_active': CookieProfile.get_value(request, CookieProfile.COOKIE_PROFILE),
    'profile_dict': CookieProfile.get_values(request),
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
  LOCATION = 'location'

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
    
    with open('gamechanger_cookie_profile.csv', 'w',newline='\n') as csvoutput:
      fieldnames = CookieProfile.values
      writer = csv.DictWriter(csvoutput, fieldnames=fieldnames)
      writer.writeheader()
      writer.writerow(
        request.session[CookieProfile.COOKIE_PROFILE],
        request.session[CookieProfile.USER_CONSENT],
        request.session[CookieProfile.ALIAS],
        request.session[CookieProfile.EMAIL],
        request.session[CookieProfile.PHONE],
        request.session[CookieProfile.CONATCT_NOTES],
        request.session[CookieProfile.SPOKEPERSON_CONSENT],
        request.session[CookieProfile.ORGANIZATION],
        request.session[CookieProfile.COUNTRY],
        request.session[CookieProfile.LOCATION],
        )

    return

  
  def createprofile(request):
    data = request.POST
    print(data)

    for item in data:
      if item in CookieProfile.keys:
        print(item, data[item])
        request.session[item] = data[item]

    if data[CookieProfile.USER_CONSENT] == 1:
      print("send to FFF")

    return redirect('action:login_cookie_profile')

  class profile_form(Form):
    CONSENT_NO=0
    CONSENT_YES=1
    _consent_options=[
      (CONSENT_NO, "NO: I do not agree that (FFF) store my personal information."),
      (CONSENT_YES, "YES: I agree that (FFF) store my personal information (until I tell FFF to remove it). We (FFF) will use the information to potentialy get in touch with you."),
    ]
    user_consent = ChoiceField(choices = _consent_options, label="Registration Consent",help_text=f"{_consent_options[CONSENT_NO][1]} <br/> {_consent_options[CONSENT_YES][1]}" , required=True)
    
    SPOKEPERSON_PRIVATE=0
    SPOKEPERSON_MEDIA=1
    SPOKEPERSON_PUBLIC=2
    _spokeperson_options = [
      (SPOKEPERSON_PRIVATE, "Private: No, I do not wish my registration identity (name, email, phone) to be known to people outside FFF."),
      (SPOKEPERSON_MEDIA, "Media: Yes, I volunteer to be a media spokesperson. I agree that my contact information (name, email, phone, country, city, notes) may be given to media representatives."),
      (SPOKEPERSON_PUBLIC, "Public: Yes, I volunteer to be a public organizer and spokesperson. Share my contact details (name, email, phone, country, city, notes) on the web, on maps, in social media, traditional media, etc.")
    ]
    spokeperson_consent=ChoiceField(choices=_spokeperson_options,help_text=f"{_spokeperson_options[SPOKEPERSON_PRIVATE][1]}<br/>{_spokeperson_options[SPOKEPERSON_MEDIA][1]}<br/>{_spokeperson_options[SPOKEPERSON_PUBLIC][1]}")
    
    alias = CharField(label="Name/Alias")
    email = EmailField(label="Email")
    phone=CharField()
    contact_notes=CharField()

    organization = ModelChoiceField(widget=autocomplete.ModelSelect2(url='/action/organization-autocomplete/'), queryset=Organization.objects.all().order_by('name'))
    
    country = ModelChoiceField(widget=autocomplete.ModelSelect2(url='/action/country-autocomplete/'), queryset=Country.objects.all().order_by('name'))
    location = ModelChoiceField(widget=autocomplete.ModelSelect2(url='/action/location-incountry-filter/', forward=['gathering_country']), queryset=Location.objects.exclude(in_country=Country.Unknown()).order_by('name'))
