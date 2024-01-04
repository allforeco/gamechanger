import googlemaps

gmaps = googlemaps.Client(key='AI**SyCEh41WFbT1Lt-fmbqlx5-HBprKsosbUrs')

# Geocoding an address
geocode_result = gmaps.geocode('1600 Amphitheatre Parkway, Mountain View, CA')

# Look up an address with reverse geocoding
reverse_geocode_result = gmaps.reverse_geocode((40.714224, -73.961452))


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