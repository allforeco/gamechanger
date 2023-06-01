import os
import sys
import json
import logging
import googlemaps
import datetime
from typing import *
from abc import ABC, abstractmethod
from action.models import Location, Organization, Gathering, Gathering_Witness
from .location_finder import LocationLookup_GoogleMaps

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
                api_key (str): Key for the Google maps API

            Returns:
                parsed_tweet (Dict): Parsed tweet with updated location and organisation data

            Example:

        """
        pass


class T4FActionRecorder(ActionRecorder):
    """ INSERT CLASS DESCRIPTION & ARGUMENTS + EXAMPLE HERE

    """

    def __init__(self) -> None:
        '''
        Initialise the ActionRecorder instance.
        '''
        super(T4FActionRecorder, self).__init__()
        self.City = None
        self.State = None
        self.Country = None

    def __call__(self, parsed_tweet: Dict, api_key: str) -> Dict:
        """ Record an action to the database

            Args:
                parsed_tweet (Dict): Parsed tweet
                api_key (str): Key for the Google maps API

            Returns:
                The location found and...
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
        eOrg = None
        if parsed_tweet["response"] == "success":
            # First try to find the organisation.
            # FIXME OPTION: name= : For case sensitive lookup
            eOrg = Organization.objects.filter(name__iexact=parsed_tweet["data"]["organization"]).first()
            if eOrg is None:
                parsed_tweet["errors"] = AddError_v2(parsed_tweet["errors"], "organization_not_found")
                parsed_tweet["response"] = "failed"
                return parsed_tweet # No need to look for location if Organisation failed
        # Let's try to find the location
        eFinal_location, parsed_tweet = self.find_location(parsed_tweet, api_key)
        # Check again to determine the location was found
        if parsed_tweet["response"] == "success":
            witness_id = None  # FIXME add twiff as witness???
            # Find the latest gathering for the location
            gathering = Gathering.objects.filter(location=eFinal_location, organizations=eOrg).order_by('-start_date')
            if len(gathering) == 0:
                gathering = Gathering.objects.filter(location=eFinal_location).order_by('-start_date')
                if len(gathering) == 0:
                    # A location can exist (e.g. a state) when no gathering was made for the location.
                    parsed_tweet["errors"] = AddError_v2(parsed_tweet["errors"], "no_gathering_found")
                    parsed_tweet["response"] = "failed"
                    return parsed_tweet
            witness = Gathering_Witness(gathering=gathering[0])
            # RuntimeWarning: DateTimeField Gathering_Witness.updated received a naive datetime (2021-05-07 11:52:41.502616) while time zone support is active.
            witness.date = datetime.datetime.strptime(parsed_tweet["data"]["created_at"], '%d-%m-%Y').replace(
                tzinfo=datetime.timezone.utc)
            witness.participants = parsed_tweet["data"]["num_people"]
            witness.proof_url = parsed_tweet["data"]["url"]
            witness.organization = eOrg
            witness.updated = datetime.datetime.today()
            witness.save()
        # Report back which org and location were recorded
        if eOrg:
            parsed_tweet["data"]["organization"] = eOrg.name
        if eFinal_location:
            parsed_tweet["data"]["location"] = eFinal_location.name
            loc = eFinal_location
            while loc.in_location is not None:
                loc = loc.in_location
                parsed_tweet["data"]["location"] = parsed_tweet["data"]["location"] + ", " + loc.name
        return parsed_tweet

    def find_location(self, parsed_tweet: Dict, api_key: str) -> Tuple[Any, Dict]:
        """ find the given location

            Args:
                parsed_tweet (Dict): Parsed tweet
                api_key (str): Key for the Google maps API

            Returns:
                The location found and...
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

        loc_finder = LocationLookup_GoogleMaps(api_key)
        loc, error = loc_finder(parsed_tweet["data"]["location"])
        if error is not None and error != "":
            log.info("Lookup error: " + error)
            parsed_tweet["errors"] = AddError_v2(parsed_tweet["errors"], error)
            parsed_tweet["response"] = "failed"
        else:
            if loc is None:
                parsed_tweet["errors"] = AddError_v2(parsed_tweet["errors"], "canonical_filter_failure")
                parsed_tweet["response"] = "failed"
                log.info("canonical_filter_failure")
                return loc, parsed_tweet
            loc_for_string = loc
            location_string = ""
            while loc_for_string.in_location is not None:
                location_string = location_string + loc_for_string.name + ", "
                loc_for_string = loc_for_string.in_location
            location_string = location_string + loc_for_string.name
            parsed_tweet["data"]["location"] = location_string
            log.info("GC location: " + location_string)
        return loc, parsed_tweet


def AddError_v2(errors: list, newError: str) -> []:
    if errors is None:
        errors = [newError]
    else:
        errors.append(newError)
    return errors
