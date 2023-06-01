import json
from pathlib import Path
from typing import *
import logging
import googlemaps
from datetime import datetime
from action.models import Location, Gmaps_LookupString, Gmaps_Locations

log = logging.getLogger(__name__)


class LocationLookup_GoogleMaps:
    def __init__(self, api_key) -> None:
        """ Find a location from a lookup string in the database

            Args:
                api_key (str): Key for the Google maps API

            Returns:
                None
        """

        super(LocationLookup_GoogleMaps, self).__init__()
        # Fetch the config
        with open(Path("/home/deploy/gamechanger/twiff2/scripts/search/location_lookup_config.json"), 'r', encoding="utf-8") as fp:
            self.config = json.load(fp)
        self.gmaps = googlemaps.Client(key=api_key)

    def __call__(self, lookup_string: str) -> Tuple[any, str]:
        """ Find the location in the database using a lookup string

            Args:
                lookup_string (str): The location to find

            Returns:
                The location found (any), None if none found
                Error (str), None if there were no errors, possible errors:
                    - api_lookup_failure
                    - location_not_found
                    - canonical_filter_failure

            NOTES:
                2 step process:
                    1 see if we already have this lookup string, else use google to find location ID
                    2 see if the location ID is already known, otherwise use google information to create a new entry
        """

        # Find the location key
        # lookup if the location is known in the Gmaps_LookupString data table
        log.info("Looking up location: " + lookup_string)
        lookup = Gmaps_LookupString.objects.filter(lookup_string=lookup_string).first()
        if lookup is None:
            # if not in database, request google for location.
            log.info("Using API")
            try:
                geocode_result = self.gmaps.geocode(address=lookup_string, language="en")
                geocode_result = geocode_result[0]
                location_key = geocode_result["place_id"]
            except:
                return None, "api_lookup_error"
            # Try to find the Geo code in the Gmaps_Locations datatable
            gmap_loc = Gmaps_Locations.objects.filter(place_id=location_key).first()
            if gmap_loc is None:
                log.info("Creating new location: " + geocode_result["formatted_address"])
                loc, error = self.create_new_location(self.config, geocode_result)
                if error is not None and error != "":
                    return None, error
                gmap_loc = Gmaps_Locations(place_id=location_key, location=loc)
                gmap_loc.save()
            else:
                log.info("Using existing location")
                loc = gmap_loc.location
            # This location is now / already known, create an entry in lookup table
            lookup = Gmaps_LookupString(lookup_string=lookup_string, Gmaps_Location=gmap_loc)
            lookup.save()
        else:
            log.info("Using Database")
            gmap_loc = lookup.Gmaps_Location
            loc = gmap_loc.location

        return loc, None

    def create_new_location(self, config: dict, loc_data: dict) -> Tuple[any, str]:
        """ Find the location in the database using a lookup string

            Args:
                config (dict): The configuration data to create a new location
                loc_data (dict): The data of the location to create

            Returns:
                The location found (any), None if none found
                Error (str), None if there were no errors, possible errors:
                    - canonical_filter_failure
                    - location_not_found

        """
        # Find the country and load its settings
        data: dict = {}
        # Start from the end, this is the biggest location: e.g. Earth, Europe, UK, England, London, some street
        i = len(loc_data["address_components"]) - 1
        has_postal_town = False
        settings: dict = None
        overrides: dict = None
        level_names: dict = config["level_names"]
        # Location types that always need to be included in the location string
        always_do_types = ["country", "postal_town", "locality", "route", "establishment"]
        while i >= 0:
            if "country" in loc_data["address_components"][i]["types"]:
                overrides = config["overrides"]
                if loc_data["address_components"][i]["long_name"] in overrides:
                    settings = overrides[loc_data["address_components"][i]["long_name"]]
            # also check for a second rule: postal_town *or* locality, locality preferred
            if "postal_town" in loc_data["address_components"][i]["types"]:
                has_postal_town = True
            if "locality" in loc_data["address_components"][i]["types"] and has_postal_town:
                always_do_types = ["country", "locality", "route", "establishment"]
            i = i - 1

        # Create the location string
        i = len(loc_data["address_components"]) - 1
        # End location should be the location type
        types: [] = loc_data["types"]
        if types[0] == "political":
            end_type = types[-1]
        else:
            end_type = types[0]
        while i >= 0:
            include = False
            param_name = "long_name"
            address_component = loc_data["address_components"][i]
            if address_component["types"][0] == "political":
                current_type = address_component["types"][-1]
            else:
                current_type = address_component["types"][0]
            if current_type in always_do_types and current_type in level_names:
                include = True
            if settings is not None:
                if current_type + "_include" in settings:
                    include = settings[current_type + "_include"]
                if current_type + "_type" in settings:
                    param_name = settings[current_type + "_type"]
            if current_type == end_type:
                include = True
            if include:
                loc_to_add = loc_data["address_components"][i][param_name]
                level = level_names[current_type]
                data[level] = loc_to_add
                if overrides is not None:
                    if loc_to_add in overrides:
                        overrides = overrides[loc_to_add]
                        if "country" in overrides:
                            data["country"] = overrides["country"]
                        if "state" in overrides:
                            data["state"] = overrides["state"]
                        if "city" in overrides:
                            data["city"] = overrides["city"]
                        if "sublocation" in overrides:
                            data["sublocation"] = overrides["sublocation"]
                        if "reload" in overrides:
                            if overrides["reload"]:
                                overrides, settings = self.reload_overrides(data, config["overrides"])
                    else:
                        overrides = None
            i = i - 1
        try:
            if "country" in data:
                log.info("Trying to find country: " + data["country"])
                loc_country = Location.objects.filter(name=data["country"], in_location=None).first()
                if loc_country is None:
                    return None, "location_not_found"
                log.info("Found country: " + loc_country.name)
            else:
                return None, "canonical_filter_failure"
            if "state" in data:
                log.info("Trying to find state: " + data["state"])
                loc_state = Location.objects.filter(name=data["state"], in_location=loc_country).first()
                if loc_state is None:
                    return None, "location_not_found"
                log.info("Found state: " + loc_state.name)
            else:
                loc_state = loc_country
            if "city" in data:
                log.info("Trying to find city: " + data["city"])
                loc_city = Location.objects.filter(name=data["city"], in_location=loc_state).first()
                if loc_city is None:
                    return None, "location_not_found"
                log.info("Found city: " + loc_city.name)
            else:
                loc_city = loc_state
            if "sublocation" in data:
                log.info("Trying to find sublocation: " + data["sublocation"])
                loc_sublocation = Location.objects.filter(name=data["sublocation"], in_location=loc_city).first()
                if loc_sublocation is None:
                    return None, "location_not_found"
                log.info("Found sublocation: " + loc_sublocation.name)
            else:
                loc_sublocation = loc_city
            return loc_sublocation, None
        except:
            return None, "location_not_found"

    @staticmethod
    def reload_overrides(data: dict, overrides: dict) -> Tuple[dict, dict]:
        # Reload the overrides and settings because a different location path must be chosen
        # Returns tuple(overrides, settings)

        settings: dict = overrides[data["country"]]
        overrides = settings
        if overrides is not None:
            if "state" in data:
                overrides = overrides[data["state"]]
        if overrides is not None:
            if "city" in data:
                overrides = overrides[data["city"]]
        if overrides is not None:
            if "sublocation" in data:
                overrides = overrides[data["sublocation"]]

        return overrides, settings
