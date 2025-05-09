from django.template import loader
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.forms import *
from django.contrib.postgres.search import TrigramSimilarity

from .bigredbutton import BigRedButton
from .parsers import geoParser

from dal import autocomplete
import base64, hashlib, datetime, googlemaps, json, os

from .models import Gathering, Gathering_Belong, Organization, OrganizationContact, Location, Country, UserHome
from .cookie_profile import CookieProfile

publicuse = True

def default_CreateSubmit_Response(request, form, title, url, feedback = None):
  template = loader.get_template('action/form_CreateSubmit.html')
  context = {
    'form': form, 
    'createsubmit_title': title, 
    'formaction_url': url, 
    'feedback': feedback, 
  }
  return HttpResponse(template.render(context, request))

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
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:permission_denied')

  return default_CreateSubmit_Response(request, GatheringCreateForm(), "Gathering", "create_gathering")
  #template = loader.get_template('action/form_CreateSubmit.html')
  #context = {'form': GatheringCreateForm(), 'createsubmit_title': "Event", 'formaction_url': "create_gathering"}
  #return HttpResponse(template.render(context, request))

'''
___create gathering by form data
___redirect loop
'''
def GatheringCreate(request):
  logginbypass = publicuse
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:permission_denied')
  data = request.POST

  try:
    regid = base64.urlsafe_b64encode(hashlib.md5(str(data['gathering_type']+":"+data['location']+":"+data['start_date']).encode()).digest()).decode()[:8]
    gathering_type = data['gathering_type']
    location = Location.objects.get(id=data['location']) or Location.objects.get(id=Location.UNKNOWN)
    start_date = datetime.datetime.strptime(data['start_date'], "%Y-%m-%d")
    duration = datetime.timedelta(weeks=int(data['duration']))
    end_date =  start_date+duration
    expected_participants = data['expected_participants']
    #organizations.add(Organization.objects.get(id=Organization.UNKNOWN))#data['organizations'] or 
    address = data['address']
    time = data['time']
    consent = data['consent']
  except:
    return default_CreateSubmit_Response(request, GatheringCreateForm(), "Gathering", "create_gathering", "Gathering Creation Error")
    #return redirect('action:gathering_submit')
  
  if consent == False:
    return default_CreateSubmit_Response(request, GatheringCreateForm(), "Gathering", "create_gathering", "Innsuficient consent to create Gathering")
    #return redirect('action:gathering_submit')
  
  gathering = Gathering()
  gathering.regid = regid #= models.CharField(primary_key=True, max_length=8, editable=False)
  gathering.gathering_type = gathering_type #= models.CharField(max_length=4, choices=_gathering_type_choices, default=STRIKE)
  gathering.location = location #= models.ForeignKey(Location, on_delete=models.SET_NULL, blank=True, null=True)
  gathering.start_date = start_date #= models.DateField(blank=True,null=True)
  gathering.duration = duration #= models.DurationField(blank=True, null=True)
  gathering.end_date = end_date #= models.DateField(blank=True,null=True)
  gathering.expected_participants = expected_participants #= models.PositiveIntegerField(blank=True, null=True)
  #gathering.organizations.add(Organization.objects.get(id=Organization.UNKNOWN))#data['organizations'] or  #= models.ManyToManyField(Organization, blank=True)
  gathering.address = address #= models.CharField(blank=True, max_length=64)
  gathering.time = time #= models.CharField(blank=True, max_length=32)
  gathering.save()
  belong = Gathering_Belong.objects.filter(regid = regid).first()
  if not belong:
    belong = Gathering_Belong(regid=regid, gathering=gathering)
    belong.save()


  print(gathering.data_all())
  return default_CreateSubmit_Response(request, GatheringCreateForm(), "Gathering", "create_gathering", "Gathering successfully created")
  #return redirect('action:gathering_submit')


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
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:permission_denied')
  
  try:
    data = request.POST
    print(f'OrgCreateSubmit {data}')
    feedback = "Group creation Error"
    name = data.get('name')
    if name:
      organization = Organization()
      organization.name = name
      organization.verified = False
      organization.save()
      print(f'OrgCreated "{name}"')
      feedback = f"Group '{name}' created"

  except Exception as e:
    print(f'OrgCreate Exception {e}')
    #redirect('action:organization_submit')

  template = loader.get_template('action/form_CreateSubmit.html')
  context = {
    'form': OrganizationCreateForm(), 
    'createsubmit_title': "Group", 
    'search_formaction_url': "create_organization", 
    'submit_formaction_url': "submit_organization", 
    'feedback': feedback, 
    'similar_ones': [],
    'total_similar_count': 0,
    'org_name': name,
    'already_exists': False,
    'created': True,
  }
  return HttpResponse(template.render(context, request))

'''
___Organization create by form
___contact redirect
'''
def OrganizationCreate(request):
  logginbypass = publicuse
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:permission_denied')
  data = request.POST
  print(f'OrgCreate {data}')

  try:
    orgs = []
    feedback = ""
    count_similar_orgs = 0
    already_exists = False

    name = data.get('name')
    if name:
      #if Organization.objects.filter(name__iexact=name).count():
      #  already_exists = False#True
      #else:
        #orgs = Organization.objects.filter(name__trigram_similar=name).filter(similarity__gt=0.1).order_by('-similarity')
        similarity_threshold = .3
        count_similar_orgs = Organization.objects.annotate(
          similarity=TrigramSimilarity('name', name),
        ).filter(similarity__gt=similarity_threshold).count()
        while similarity_threshold < 1:
          orgs = Organization.objects.annotate(
            similarity=TrigramSimilarity('name', name),
          ).filter(similarity__gt=similarity_threshold).order_by('-similarity')
          if orgs.count() < 20:
            break
          similarity_threshold += .1
        similarity_threshold -= .1
        orgs = Organization.objects.annotate(
          similarity=TrigramSimilarity('name', name),
        ).filter(similarity__gt=similarity_threshold).order_by('-similarity')[:10]
        print(f"Found {count_similar_orgs} similarly named orgs, here are the top {orgs.count()}: {orgs}")
  except Exception as e:
    print(f'OrgCreate Exception {e}')
    feedback = "Group creation Error"
    #redirect('action:organization_submit')

  template = loader.get_template('action/form_CreateSubmit.html')
  context = {
    'form': OrganizationCreateForm(), 
    'createsubmit_title': "Group", 
    'search_formaction_url': "create_organization", 
    'submit_formaction_url': "submit_organization", 
    'feedback': feedback, 
    'similar_ones': orgs,
    'total_similar_count': count_similar_orgs,
    'org_name': name,
    'already_exists': already_exists,
  }
  return HttpResponse(template.render(context, request))

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
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:permission_denied')
  
  return default_CreateSubmit_Response(request, OrganizationcontactCreateForm(), "Organization Contact", "create_organizationcontact")
  #template = loader.get_template('action/form_CreateSubmit.html')
  #context = {'form': OrganizationcontactCreateForm(), 'createsubmit_title': "Organization Contact", 'formaction_url': "create_organizationcontact"}
  #return HttpResponse(template.render(context, request))

'''
___create contact by form data
___redirect loop
'''
def OrganizationcontactCreate(request):
  logginbypass = publicuse
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:permission_denied')
  data = request.POST
  print(data)

  try:
    contacttype= data['contacttype']
    address=data['address']
    info=data['info']
    organization=Organization.objects.get(id=data['organization'])
    location=Location.objects.get(id=data['location'])
  except:
    return default_CreateSubmit_Response(request, OrganizationcontactCreateForm(), "Organization Contact", "create_organizationcontact", "Organization Vcongtgact creatiion Error")
    #return redirect('action:organizationcontact_submit')
  
  organizationcontact = OrganizationContact()
  organizationcontact.contacttype = contacttype
  organizationcontact.address = address
  organizationcontact.info = info
  organizationcontact.organization=organization
  organizationcontact.location=location
  organizationcontact.save()

  return default_CreateSubmit_Response(request, OrganizationcontactCreateForm(), "Organization Contact", "create_organizationcontact", "Organization Contact successfully created")
  #return redirect('action:organizationcontact_submit')



class LocationCreateForm(ModelForm):
  class Meta():
    model = Location
    fields = ['name']

'''
___formclass location
'''
class LocationParseForm(Form):
  #country = CharField(required=True)
  #state = CharField(required=False)
  #county = CharField(required=False)
  #town = CharField(required=False)
  address = CharField(required=False, help_text="ex. \"street, town, county, state, country\"")
  #lat = FloatField()
  #lon = FloatField()

def LocationCreateSubmit(request):
  #publicuse = False
  logginbypass = publicuse
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:permission_denied')
  
  return default_CreateSubmit_Response(request, LocationParseForm(), "Location", "create_location")
  #template = loader.get_template('action/form_CreateSubmit.html')
  #context = {'form': LocationParseForm(), 'createsubmit_title': "Location", 'formaction_url': "create_location"}
  #return HttpResponse(template.render(context, request))

def LocationMapCreateSubmit(request):
  logginbypass = publicuse
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:permission_denied')
  
  return default_CreateSubmit_Response(request, LocationParseForm(), "Location", "create_location", "Location successfully created")
  #template = loader.get_template('action/form_CreateSubmit_location.html')
  #context = {"google_maps_key": geoParser.gkey}
  #return HttpResponse(template.render(context, request))

def LocationMapCreateSubmit(request):
  logginbypass = publicuse
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:permission_denied')
  template = loader.get_template('action/form_CreateSubmit_location.html')
  context = {"google_maps_key": geoParser.gkey}
  return HttpResponse(template.render(context, request))

def LocationCreate(request):
  
  def in_metadata(d, lvl):
    lvl+=1
    t = type(d)
    if t is str:
      for i in range(lvl):
        print(">", end='')
      print(d)
    elif t is dict:
      keys = d.keys()
      for key in keys:
        for i in range(lvl):
          print("#", end='')
        print(key)
        in_metadata(d[key], lvl)
    elif t is list:
      for i in d:
        in_metadata(i, lvl)
    else:
      for i in range(lvl):
        print(">", end='')
      print(d)

  data = request.POST
  print(f'LocCreate {data}')

  try:
    locs = []
    feedback = ""
    formatted_address = ""
    gloc_lat = None
    gloc_lon = None
    gloc_path = ""
    gloc_postcode = None
    count_similar_locs = 0
    would_create_names = []
    already_exists = False

    name = data.get('name')
    search_name = data.get('search_name', "")
    create_names = data.get('create_names')

    if name:
      similarity_threshold = .3
      count_similar_locs = Location.objects.annotate(
        similarity=TrigramSimilarity('name', name),
      ).filter(similarity__gt=similarity_threshold).count()
      while similarity_threshold < 1:
        locs = Location.objects.annotate(
          similarity=TrigramSimilarity('name', name),
        ).filter(similarity__gt=similarity_threshold).order_by('-similarity')
        if locs.count() < 20:
          break
        similarity_threshold += .1
      similarity_threshold -= .1
      locs = Location.objects.annotate(
        similarity=TrigramSimilarity('name', name),
      ).filter(similarity__gt=similarity_threshold).order_by('-similarity')[:10]
      print(f"Found {count_similar_locs} similarly named locs, here are the top {locs.count()}: {locs}")
  except Exception as e:
    print(f'LocCreate Exception {e}')
    feedback = "Location creation Error"
    #redirect('action:organization_submit')

  try:
    if search_name:
      name = search_name
    if name:
      google_metadata = geoParser.gmaps.geocode(name)
      print(len(google_metadata), google_metadata)

      if len(google_metadata) < 1:
        feedback = 'Google Maps does not recognize this place name.'
      elif len(google_metadata) == 1:
        formatted_address = google_metadata[0]['formatted_address']
        gloc_path = ", ".join([ac['long_name'] for ac in google_metadata[0]['address_components']])
        gloc_lat = google_metadata[0]['geometry']['location']['lat']
        gloc_lon = google_metadata[0]['geometry']['location']['lng']
        gloc_postcode = None
        try:
          gloc_postcode = [pc for pc in google_metadata[0]['address_components'] if 'postal_code' in pc['types']][0]['long_name']
          postcode_offset = formatted_address.find(gloc_postcode)
          if postcode_offset >= 0:
            # Remove postcode from formatted_address
            formatted_address = formatted_address[:postcode_offset]+formatted_address[postcode_offset+len(gloc_postcode)+1:]
        except Exception as e:
          pass # Did not find any postcode to remove
      else: # more than 1
        feedback = 'Google Maps recognizes multiple places by this name, please be more specific.'
  except Exception as e:
    print(f'LocCreate Exception2 {e}')
    feedback = "Location creation Error"

  if formatted_address:
    address_parts = [part.strip() for part in formatted_address.split(",")]
    # 1st part: country
    country_name = address_parts.pop()
    country_objs = Country.objects.filter(name__iexact=country_name)
    if country_objs.count() != 1:
      feedback = f"Country {country_name} is not in the database. Contact an admin to have it added."
      print(feedback)
    else:
      country_loc = Location.objects.filter(name__iexact=country_name, in_location__isnull=True)
      if country_loc.count() != 1:
        feedback = f"Location {country_name} is not in the database. Contact an admin to have it added."
        print(feedback)
      else:
        parent_loc = country_loc.first()
        parent_name = country_name
        while address_parts:
          part_name = address_parts.pop()
          next_loc = Location.objects.filter(name__iexact=part_name, in_location=parent_loc)
          if next_loc.count() == 0:
            if create_names: # go ahead and create
              if part_name in create_names:
                print(f'Creating {part_name} in {parent_name}')
                new_loc = Location(
                  name = part_name,
                  in_country = country_objs.first(),
                  in_location = parent_loc,
                  zip_code = gloc_postcode,
                  lat = gloc_lat,
                  lon = gloc_lon,
                )
                new_loc.save()
                feedback = f"{part_name} created in {parent_name}."
              else:
                feedback = f"{part_name} not authorized for creation, aborted"
                print(feedback)
            else: # just figure out what needs to be created
              print(f'Would create {part_name} in {parent_name}')
              would_create_names += [part_name]
            parent_loc = None
          else:
            print(f'Found existing {part_name} in {parent_name}')
            parent_loc = next_loc.first()
          parent_name = part_name

  template = loader.get_template('action/location_create.html')
  context = {
    'form': LocationCreateForm(), 
    'createsubmit_title': "Location", 
    'search_formaction_url': "create_location", 
    'submit_formaction_url': "submit_location", 
    'search_name': name if name else "",
    'feedback': feedback, 
    'similar_ones': locs,
    'total_similar_count': count_similar_locs,
    'loc_name': name,
    'gloc_name': formatted_address,
    'gloc_path': gloc_path,
    'gloc_lat': gloc_lat,
    'gloc_lon': gloc_lon,
    'create_names': ", ".join(would_create_names),
    'already_exists': already_exists,
  }
  return HttpResponse(template.render(context, request))


  #publicuse = False
  logginbypass = publicuse
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:permission_denied')
  data = request.POST
  #print(data)
  address = data['address']
  if not data['address'] or len(data['address']) < 3:
    return default_CreateSubmit_Response(request, LocationParseForm(), "Location", "create_location", "Enter a full address")
    return redirect('action:location_submit')
  if not geoParser.gkey: return default_CreateSubmit_Response(request, LocationParseForm(), "Location", "create_location", "Google maps function disabled. Try again later")
  google_metadata = geoParser.gmaps.geocode(address)
  #print(len(google_metadata), google_metadata)

  if len(google_metadata) < 1:
    return default_CreateSubmit_Response(request, LocationParseForm(), "Location", "create_location", "Invalid address")
    return redirect('action:location_submit')
    
  if len(google_metadata) > 1:
    addresses = list()
    for l in google_metadata:
      ln = ""
      for li in google_metadata[0]['address_components']:
        ln += li['long_name'] + ", "
        ln = ln.rstrip(" ,")
        address.append(ln)
    template = loader.get_template('action/form_CreateSubmit.html')
    class select_form(Form):
      _address_options = addresses
      address = ChoiceField(choices=_address_options, label="Select the specific address")
    context = {'form':select_form, 'createsubmit_title': "Select Specific Address", 'formaction_url': "create_location"}
    return HttpResponse(template.render(context, request))
    
  location_typefilter = ['establishment', 'park', 'point_of_interest', 'political']

  in_country = Country()
  for ln in google_metadata[0]['address_components']:
    if "country" in ln['types']:
      if Country.objects.filter(name=ln['long_name']).exists():
        in_country = Country.objects.filter(name=ln['long_name']).first()
      else:
        in_country = Country.generateNew(ln['long_name'])

  #print("gmac")
  #Create locations, unlinked
  location_list = []
  for ln in google_metadata[0]['address_components']:
    if any(t in ln['types'] for t in location_typefilter):
      print("ln", ln['long_name'])
      l = Location()
      l.name = ln['long_name']
      l.in_country = in_country
      l.in_location = Location.Unknown()
      l.zip_code = None
      l.lat = google_metadata[0]["geometry"]["location"]["lat"]
      l.lon = google_metadata[0]["geometry"]["location"]["lng"]
      verificationusertag = "?"
      if request.user.is_authenticated:
        verificationusertag = "@"
        verificationusertag += request.user.get_username()
      elif CookieProfile.get_value(request, CookieProfile.COOKIE_PROFILE):
        verificationusertag = "#"
        verificationusertag += CookieProfile.get_value(request, CookieProfile.ALIAS)
      l.creation_details = verificationusertag
      l.google_metadata = str(google_metadata[0])[:2047]

      location_list.insert(0, l)

  if Location.objects.filter(in_country=in_country, name=location_list[0].name).exists():
    location_list[0] = Location.objects.filter(in_country=in_country, name=location_list[0].name).first()
  else:
    location_list[0].save()
  for ln in location_list:
    #print(ln, location_list.index(ln))
    i = location_list.index(ln)
    if Location.objects.filter(in_country=in_country, in_location=location_list[max(0, i-1)], name=ln.name).exists():
      location_list[i] = Location.objects.filter(in_country=in_country, in_location=location_list[max(0, i-1)], name=ln.name).first()
    else:
      if (i-1 == -1):
        ln.in_location = Location.Unknown()
      else:
        ln.in_location = location_list[max(0, i-1)]
      ln.save()
      
  #print("nl", in_location_data_list)

  def metadataToLocation(metadata):
    location = Location()
    location.name=metadata[0]
    #print("lmn:", location.name)

    country_name = metadata[1]
    location.in_country=Country.objects.filter(name__iexact=country_name).first() or Country.Unknown()
    #print("lic:",location.in_country.name)

    in_location_name = metadata[2]
    location.in_location = Location.objects.filter(name__iexact=in_location_name).first() or Location.Unknown()
    #print("lil:",location.in_location.name)

    location.zip_code=metadata[3]

    location.lat=metadata[4][0]
    location.lon=metadata[4][1]
    #print("lll",location.lat, location.lon)

    location.creation_details=metadata[5]
    #print("lvr",location.verified)

    location.google_metadata = metadata[6]

    if location.name == None or location.in_location == None or location.in_country == None:
      #print("ler: Fail")
      return default_CreateSubmit_Response(request, LocationParseForm(), "Location", "create_location", "Creation Fail")
    location.save()
    #print(f"Location:\n\t{location.name}\n\t{location.in_country}\n\t{location.in_location}\n\t[{location.lat},{location.lon}]\n\t,location.google_metadata")

    #in_location_data_list.reverse()

  #print("ildl")
  #for ln in in_location_data_list:
    #print("ln", ln)
    #i = in_location_data_list.index(ln)
    #print("ln", i, ln[0], ":", in_location_data_list[i][0])
    #metadataToLocation(ln)
    #if not Location.objects.filter(in_location=Location.objects.filter(name__iexact=in_location_data_list[i]).first(), name__iexact=ln):
    
  return default_CreateSubmit_Response(request, LocationParseForm(), "Location", "create_location", f"Location ({address}), succssessfully created")#return redirect('action:location_submit')

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
  ##JANL gathering_location = ModelChoiceField(widget=autocomplete.ModelSelect2(url='/action/location-incountry-filter/', forward=['gathering_country']), queryset=Location.objects.exclude(in_country=Country.Unknown()).order_by('name'))
  gathering_location = ModelChoiceField(widget=autocomplete.ModelSelect2(url='/action/location-incountry-filter/', forward=['gathering_country']), queryset=Location.objects.order_by('name'))
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
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:permission_denied')

  template = loader.get_template('action/form_USG_CreateSubmit.html')
  context = {
    'form_user': USGformuser(), 
    'form_spokeperson': USGformspokeperson(), 
    'form_gathering': USGformgathering()
    }
  return HttpResponse(template.render(context, request))

def USGCreate(request):
  logginbypass = publicuse
  if not (request.user.is_authenticated or (logginbypass and not BigRedButton.is_emergency())): return redirect('action:permission_denied')
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