import os
import sys
import json
import logging
import googlemaps
import datetime
from pathlib import Path
from typing import *
from abc import ABC, abstractmethod
from .geodata import Geodata

sys.path.append('/home/deploy/gamechanger/gamechanger')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gamechanger.settings")
from django.conf import settings
sys.path.append('/home/deploy/gamechanger/action')
from models import Location, Organization, Gathering, Gathering_Witness, Gmaps_LookupString, \
    Gmaps_Locations


log = logging.getLogger(__name__)


class ActionRecorder(ABC):
    """ ...
    """

    def __init__(self) -> None:
        pass

    @abstractmethod
    def __call__(self, parsed_tweet: Dict, api_key: str) -> Dict:
        """ Record an action

            Args:
                parsed_tweet (Dict): Parsed tweet

            Returns:
                parsed_tweet (Dict): Parsed tweet with updated location and organisation data

            Example:

        """
        pass


class T4FActionRecorder(ActionRecorder):
    """ INSERT CLASS DESCRIPTION & ARGUMENTS + EXAMPLE HERE

    """

    def __init__(self, path: str) -> None:
        '''
        Initialise the ActionRecorder instance.
        '''
        super(T4FActionRecorder, self).__init__(path)
        self.City = None
        self.State = None
        self.Country = None

    def __call__(self, parsed_tweet: Dict, api_key: str) -> Dict:
        """ Record an action

            Args:
                parsed_tweet (Dict): Parsed tweet

            Returns:
                parsed_tweet (Dict): Parsed tweet with updated location and organisation data
                A new error sets the response param to failed
                New errors which could be added to the parsed tweet
                    - api_lookup_failure
                    - canonical_filter_failure
                    - organization_not_found
                    - location_not_found
                    - no_gathering_found
        """

        # Check if the parsing was done with success, otherwise we can not record anyways.
        if parsed_tweet["response"] == "success":
            # First try to find the organisation.
            # FIXME OPTION: name= : For case sensitive lookup
            eOrg = Organization.objects.filter(name__iExact=parsed_tweet["organization"]).first()
            if eOrg is None:
                parsed_tweet["errors"] = AddError_v2(parsed_tweet["errors"], "organization_not_found")
                parsed_tweet["response"] = "failed"
                return parsed_tweet # No need to look for location if Organisation failed
            # Report back which org and location were recorded
            parsed_tweet["organization"] = eOrg.name
        # Let's try to find the location
        self.gmaps = googlemaps.Client(key=api_key)
        eFinal_location, parsed_tweet = self.find_location(parsed_tweet)
        # Check again to determine the location was found
        if parsed_tweet["response"] == "success":
            witness_id = None  # FIXME add twiff as witness???
            gathering = Gathering.objects.get(location=eFinal_location, organizations=eOrg)
            if len(gathering) == 0:
                gathering = Gathering.objects.get(location=eFinal_location)
            if len(gathering) == 0:
                parsed_tweet["errors"] = AddError_v2(parsed_tweet["errors"], "no_gathering_found")
                parsed_tweet["response"] = "failed"
                return parsed_tweet
            witness = Gathering_Witness(gathering=gathering)
            # RuntimeWarning: DateTimeField Gathering_Witness.updated received a naive datetime (2021-05-07 11:52:41.502616) while time zone support is active.
            witness.date = datetime.datetime.strptime(parsed_tweet["created_at"], '%Y-%m-%d').replace(
                tzinfo=datetime.timezone.utc)
            witness.participants = parsed_tweet["num_people"]
            witness.proof_url = parsed_tweet["url"]
            witness.organization = eOrg
            witness.updated = datetime.datetime.today()
            witness.save()
        # Report back which org and location were recorded
        if eOrg:
            parsed_tweet["organization"] = eOrg.name
        if eFinal_location:
            parsed_tweet["location"] = eFinal_location.name
            loc = eFinal_location
            while loc.in_location is not None:
                loc = loc.in_location
                parsed_tweet["location"] = parsed_tweet["location"] + ", " + loc.name
        return parsed_tweet


    def find_location(self, parsed_tweet: Dict) -> Tuple[Any, Dict]:
        """ find the given location

            Args:
                parsed_tweet (Dict): Parsed tweet

            Returns:
                parsed_tweet (Dict): Parsed tweet with updated location and organisation data
                A new error sets the response param to failed
                New errors which could be added to the parsed tweet
                    - api_lookup_failure
                    - canonical_filter_failure
                    - location_not_found
            NOTES:
                2 step process:
                    1 see if we already have this lookup string, else use google to find location ID
                    2 see if the location ID is already known, otherwise use google information to create a new entry
        """

        lookup_string = parsed_tweet["data"]["location"]
        lookup = Gmaps_LookupString.objects.filter(lookup_string=lookup_string).first()
        if lookup is None:
            # If this lookup_string is not in the DB then find the location using google maps API
            try:
                geocode_result = self.gmaps.geocode(parsed_tweet["data"]["location"])[0]
                location_key = geocode_result["place_id"]
            except:
                parsed_tweet["errors"] = AddError_v2(parsed_tweet["errors"], "api_lookup_failure")
                parsed_tweet["response"] = "failed"
                # no chance of finishing the record
                return None, parsed_tweet
            gmap_loc = Gmaps_Locations.objects.filter(place_id=location_key).first()
            if gmap_loc is None:
                # The place_id from the lookup was never used before, we need to create a new location.
                loc, parsed_tweet = self.create_new_gmaps_location(geocode_result["formatted_address"], parsed_tweet)
                if loc is None:
                    return None, parsed_tweet
                gmap_loc = Gmaps_Locations(place_id=location_key, location=loc)
                gmap_loc.save()
            else:
                loc = gmap_loc.location
                # This location is now / already known, create an entry in lookup table
            lookup = Gmaps_LookupString(lookup_string=lookup_string, Gmaps_Location=gmap_loc)
            lookup.save()
        else:
            gmap_loc = lookup.Gmaps_Location
            loc = gmap_loc.location
        return loc, parsed_tweet

    def create_new_gmaps_location(self, location_string: str, parsed_tweet: Dict) -> Tuple[Any, Dict]:
        """ create a new location in the lookup datatables

            Args:
                location_string (str): formatted_address of the google maps API result
                parsed_tweet (Dict): Parsed tweet

            Returns:
                Location (Any): Location entry in the Gmaps_Locations table
                parsed_tweet (Dict): Parsed tweet with updated location and organisation data
                A new error sets the response param to failed
                New errors which could be added to the parsed tweet
                    - canonical_filter_failure
                    - location_not_found
        """

        if not self.tGoogleLoc(location_string):
            parsed_tweet["errors"] = AddError_v2(parsed_tweet["errors"], "canonical_filter_failure")
            parsed_tweet["response"] = "failed"
            return None, parsed_tweet

        # Find the correct location
        dbCountry = self.filter_location(name=self.Country, in_loc=None)
        if self.State != "":
            dbState = self.filter_location(name=self.State, in_loc=dbCountry)
        else:
            dbState = dbCountry
        if self.City != "":
            dbCity = self.filter_location(name=self.City, in_loc=dbState)
        else:
            dbCity = dbState
        final_location = None
        if dbCity is None:
            if "," in self.City:
                cityParts = self.City.split(",")
                in_loc = dbState
                for citypart in cityParts:
                    in_loc = self.filter_location(name=citypart, in_loc=in_loc)
                    if in_loc is None:
                        parsed_tweet["errors"] = AddError_v2(parsed_tweet["errors"], "location_not_found")
                        parsed_tweet["response"] = "failed"
                        return None, parsed_tweet
                if in_loc is not None:
                    final_location = in_loc
            else:
                parsed_tweet["errors"] = AddError_v2(parsed_tweet["errors"], "location_not_found")
                parsed_tweet["response"] = "failed"
                return None, parsed_tweet
        else:
            final_location = dbCity
        return final_location, parsed_tweet

    def filter_location(self, name, in_loc) -> Location:
        result = Location.objects.filter(name=name, in_location=in_loc)
        if len(result) > 0:
            return result[0]
        else:
            return None

    def tGoogleLoc(self, location_path):
        """ Cleanup the google location string

            Args:
                location_path (str): formatted_address of the google maps API result

            Returns:
                True when the function was executed as expected
                The self.Country, self.State, self.City variables.

        -------> SYNC INFO <---------
        Copied from Coffer, adapted to twiff needs, still very similar.
        If changes are needed here check whether Coffer needs changes too!
        """

        eloc = location_path
        try:
            eparts = eloc.split(", ")
        except:
            # The location is not a string..?!
            return False
        try:
            # If the "country" part is a number, remove it
            int(eparts[-1])
            eparts = eparts[:-1]
        except:
            pass
        self.Country = Geodata.get_canonical_country_name_static(Geodata.clean_zip_static(eparts[-1]))
        if Geodata.is_country_with_states_static(self.Country):
            try:
                gstate = eparts[-2].upper()
                # Remove postal number from string, and strip
                gstate = Geodata.clean_zip_static(gstate)
                self.State = Geodata.get_canonical_state_name_static(self.Country, gstate)
            except:
                self.State = ""
            eparts = eparts[:-2] # Remove country & state
        else:
            self.State = ""
            eparts = eparts[:-1] # Remove country
        self.City = ", ".join(eparts)
        return True


def AddError_v2(errors: list, newError: str) -> []:
    if errors is None:
        errors = [newError]
    else:
        errors.append(newError)
    return errors
