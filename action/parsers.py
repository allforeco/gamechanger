from .models import Location
import os, googlemaps

'''
___Google maps parser
'''
class geoParser:
  gkey = os.environ['GOOGLE_MAPS_API_KEY']
  gmaps = googlemaps.Client(key=gkey, queries_per_second=1)

  def latlonTOaddress(self, lat, lon):
    return self.gmaps.reverse_geocode((lat, lon))

  def addressTOlatlon(self, address):
    return self.gmaps.geocode(address)

  def locationTOaddress(self, id):
    if Location.objects.filter(id=id).exists():
      location = Location.objects.get(id=id)
    else:
      location = Location.Unknown()
    address = location.name
    if location.in_location.name != location.in_country.name:
      address += ", " + location.in_location.name
      inl = location
      brk = 0
      while (inl.in_location != None and inl.in_country != None):
        if inl.in_location.name == inl.in_country.name:
          address += inl.name
          break
        inl=inl.in_location
        brk+=1

    address += ", " + location.in_country.name

    return address
  
  def locationTOlatlon(self, id):
    if Location.objects.filter(id=id).exists():
      location = Location.objects.get(id=id)
    else:
      location = Location.Unknown()
    return [location.lat, location.lon]

'''
___use in mediaparser to handle media objects
'''
class MediaObject:
  def __init__(self, name, description, code, icon, urls, domains, prefix):
    self.name = name
    self.code = code
    self.icon = '/static/icon_' +icon+'.png'
    self.description = description
    self.urls = urls
    self.domains = domains
    self.prefix = prefix

  name = ""
  code = ""
  icon = ""
  description = ""
  urls = []
  domains = []
  prefix = ""

'''
___interpret links 
___assign link icons/decorations
___link validity
'''
class MediaParser:
  OTHER=MediaObject(
    "Other", "Other Media", "OTHR",
    'unknown',
    [],
    [],
    'https://')
  EMAIL=MediaObject(
    "Email", "Email Address", "MAIL",
    'mail',
    [],
    [],
    'mailto:')
  PHONE=MediaObject(
    "Phone", "Phone Number", "PHON",
    'phone',
    [],
    [],
    'tel:')
  WEBSITE=MediaObject(
    "Website", "Webb Address", "WEBS",
    'globe',
    [],
    [],
    'https://')
  YOUTUBE=MediaObject(
    "Youtube", "YouTube Address", "YOUT",
    'yt30',
    ['youtube'],
    ['.com'],
    'https://')
  TWITTER=MediaObject(
    "X (formerly Twitter)", "X (formerly Twitter) Address", "TWTR",
    'twitter30',
    ['twitter'],
    ['.com'],
    'https://')
  FACEBOOK=MediaObject(
    "Facebook", "Facebook Address", "FCBK",
    'fb30',
    ['facebook'],
    ['.com'],
    'https://')
  INSTAGRAM=MediaObject(
    "Instagram", "Instagram Address", "INSG",
    'insta30',
    ['instagram'],
    ['.com'],
    'https://')
  LINKEDIN=MediaObject(
    "LinkedIN", "LinkedIN Address", "LNIN",
    'linkedin',
    ['linkedin'],
    ['.com'],
    'https://')
  VIMEO=MediaObject(
    "Vimeo", "Vimeo Address", "VIMW",
    'vimeo',
    [],
    ['.com'],
    'https://')
  WHATSAPP=MediaObject(
    "Whatsapp", "Whatsapp Address", "WHAP",
    'whatsapp',
    ['whatsapp'],
    ['.com'],
    'https://')
  TELEGRAM=MediaObject(
    "Telegram", "Telegram Address", "TLMG",
    'telegram',
    ['t'],
    ['.me'],
    'https://')
  DISCORD=MediaObject(
    "Discord", "Discord Address", "DCRD",
    'discord',
    [],
    ['.com'],
    'https://')
  SLACK=MediaObject(
    "Slack", "Slack Address", "SLAK",
    'slack',
    [],
    ['.com'],
    'https://')

  '''
  ***WIP
  '''
  def get_Icon(self, MEDIA):
    if self._media_description[MEDIA]:
      return self._media_icon[MEDIA]
    else:
      return self._media_icon[self.OTHER]

  def checkMEDIA(self, link):
    splitlink = link.split('/')

  def checkURL(self, MEDIA, link):
    splitlink = link.split('/')
    
  def get_URL(self, MEDIA, link):
    splitlink = link.split('/')
    outlink=''

    if not self._media_description[MEDIA]:
      return self.checkURL(self, self.OTHER, link)

    if self._media_url_prefix[MEDIA][0] and not link.startswith(self._media_url_prefix[MEDIA][0]):
      outlink+=self._media_url_prefix[MEDIA]

    if self._media_url_prefix[MEDIA][1] and not link.contains(self._media_url_prefix[MEDIA][1]):
      outlink+=self._media_url_prefix[MEDIA][1]

    outlink+=link

    if self._media_url_prefix[MEDIA][2] and not link.endswith(self._media_url_prefix[MEDIA][2]):
      outlink+=self._media_url_prefix[MEDIA][1]

    return outlink

'''
???google maps parsing
'''
#class geoParser:
#  def __str__(self):
#    return "geoparser"
  #gmaps = googlemaps.Client(key='AI**SyCEh41WFbT1Lt-fmbqlx5-HBprKsosbUrs')

  # Geocoding an address
  #geocode_result = gmaps.geocode('1600 Amphitheatre Parkway, Mountain View, CA')

  # Look up an address with reverse geocoding
  #reverse_geocode_result = gmaps.reverse_geocode((40.714224, -73.961452))


  #Logger.log(reg.Town);
  #//Logger.log(approvecell);
  #var citycell = getRel(approvecell, reg.Town);
  #//Logger.log(citycell);
  #var countrycell = getRel(approvecell, reg.Country);
  #var latcell = getRel(approvecell, reg.Lat);
  #var loncell = getRel(approvecell, reg.Lon);
  #var loccell = getRel(approvecell, reg.Loc);
  #if(loncell.getDisplayValue() == '') {
    #var position = geocode_city(citycell.getValue(), countrycell.getValue());
    #if(position.isfound) {
      #approvecell.setBackgroundColor('green');
      #latcell.setValue(position.lat)
      #loncell.setValue(position.lon)
      #loccell.setValue(position.loc)
    #} else {
      #approvecell.setBackgroundColor('red');
      #latcell.setValue("Can't find city '"+citycell.getValue()+"' in '"+countrycell.getValue()+"'")
      #loncell.setValue("")
    #}
  #}
  #
  #function geocode_city(city, country) {
    #var address = city + ", " + country;
    #var pinlist = Maps.newGeocoder().geocode(address)
    #var fcity = pinlist.results[0];
    #var latlon = fcity.geometry.location;
    #return {'isfound':true, 'lat':latlon.lat, 'lon':latlon.lng, 'loc':fcity.formatted_address};
    #//for (var i = 0; i < pinlist.results.length; i++) {
    #//  var fcity = pinlist.results[i];
      #//for(var j = 0; j < fcity.address_components.length; j++) {
      #//  var comp = fcity.address_components[j];
      #//  if(comp.types.indexOf("country") >= 0) {
      #//    if(strEqNoCase(comp.long_name, country)) {
      #//      latlon = fcity.geometry.location;
      #//      return {'isfound':true, 'lat':latlon.lat, 'lon':latlon.lng, 'loc':fcity.formatted_address};
      #//    }
      #//  }
      #//}
      #return {'isfound':false}
    #//}
  #}