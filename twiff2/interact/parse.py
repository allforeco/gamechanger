import datetime
import json
import logging
from pathlib import Path

from typing import *

from abc import ABC, abstractmethod

log = logging.getLogger(__name__)


class Parser(ABC):
    """ Base Parser Class for extracting information fields from input object, specific implementations
        should override the `__call__` method for extracting data from the object (usually a freeform text
        field) and return the parser data in the user-specified format to be used by other processes.

        CONTRACT:
            Returned data should be in the following format; response generator should only attempt to create
            a response if the "response" field is "success" likewise the retweet condition is the same.

            dParsed = {"response": "success",
                       "data": {"num_people": nPeople,
                                "created_at": tDate.strftime("%d-%m-%Y"),
                                "organization": sOrganisation,
                                "location": sFullLocation,
                                "url": sURL},
                       "errors": None}

       NOTE:
            Returned key, value pairs should contain necessary information for the
            reponse_generator to select the approriate response. An example of how
            this is used is shown below.

        Args:
            tweet (Dict): Standard extended JSON tweet response.

        Returns:
            parsed_tweet (Dict): Parsed tweet data in JSON format.

        Example::
            >>> config = "/path/to/JSON"
            >>> parser = ParserChild(config)
            >>> result = parser(tweets)
    """

    def __init__(self, config: str) -> None:
        '''
        Initialise the TweetParser instance.
        '''
        # Load configuration from JSON file.
        with open(config, "r") as fp:
            self.config = json.load(fp)

    @abstractmethod
    def __call__(self, tweet: Dict) -> Dict:
        '''
        Forward method to parse the tweet and return parsed data fields.
        '''
        pass


class T4FParser(Parser):
    """ Parses tweet.

        NOTE:
            Returned key, value pairs should contain necessary information for the
            response_generator to select the appropriate response. An example of how
            this is used is shown below.

        Args:
            tweet (Dict): Standard extended JSON tweet response.

        Returns:
            parsed_tweet (Dict): Parsed tweet data in JSON format.
                response: success or failed
                tweettype: Normal or Quoted
                twiff_id: ID of a valid twiff tweet, or None
                quote_id: ID of the qouted tweet from a valid twiff tweet, or None
                data: extracted twiff data
                errors: Possible errors are:
                    hashtag_twiff_not_found
                    twifftext_too_short
                    no_org_found
                    no_country_found
                    no_city_found
                    no_people_found

        Example::
            >>> config = "/path/to/JSON"
            >>> parser = TweetParser_v2(config)
            >>> result = parser(tweets, users)
    """

    def __init__(self, config: str) -> None:
        '''
        Initialise the TweetParser_v2 instance.
        '''
        super(T4FParser, self).__init__(config)

        # Configuration
        with open('/home/deploy/gamechanger/twiff/scripts/search/ignored_users.json', "r") as fp:
            self.IgnoredUsers = json.load(fp)
        self.BannedWords = self.config['banned_words']

    def __call__(self, tweet: dict, users: dict) -> dict:
        '''
        Forward pass
        '''

        # To start parsing the twiff data, first extract some tweet data
        sTweetText = tweet["text"]
        dEntities = tweet["entities"]
        r = {"response": "failed",
             "tweettype": None,
             "twiff_id": None,
             "quote_id": None,
             "data": {"num_people": 0,
                      "created_at": "",
                      "organization": "",
                      "location": "",
                      "url": ""},
             "errors": []}
        dUrls: []
        if "urls" in dEntities:
            dUrls = dEntities["urls"]
        tTweetDate = tweet["created_at"]
        # Let's find the start of the twiff string, drop the rest, not needed
        nTwiffStart = sTweetText.find("#twiff")
        if nTwiffStart < 0:
            nTwiffStart = sTweetText.find("#Twiff")
        if nTwiffStart < 0:
            nTwiffStart = sTweetText.find("#TWIFF")
        if nTwiffStart < 0:
            r["errors"] = AddError_v2(r["errors"], "hashtag_twiff_not_found")
            return r
        sTwiffText = sTweetText[nTwiffStart:]
        # When the last URL is a display URL to a picture drop it too,
        # to prevent using the display URL as the quoted tweet parameter
        if "urls" in dEntities:
            for Url in dUrls:
                if "pic.twitter.com" in str(Url["display_url"]):
                    sDisplayUrl = str(Url["display_url"]).replace("pic.twitter.com/", "")
                    nLen = len(sTwiffText) - (len(sDisplayUrl) + 13)
                    sTwiffText = sTwiffText[:nLen]
                    break
        # Find the correct tweet URL, for the tweet displaying the action
        # It may not necessarily be the reporting tweet
        sQuoteURL = ""
        sTweetType = "Normal"  # Remember tweet type for replies
        sQuotedUserId = ""
        if "referenced_tweets" in tweet:
            dRefTweets = tweet["referenced_tweets"]
            rft = {}
            for rft in dRefTweets:
                if rft["type"] == "quoted":
                    sTweetID = rft["id"]
                    sTweetType = "Quoted"
                    for Url in dUrls:
                        if rft["id"] in str(Url["expanded_url"]):
                            sQuoteURL = Url["expanded_url"]
                            sQuotedUserName = sQuoteURL.split("/")[3]
                            sQuotedUserId = FindUserIdByName_v2(users, sQuotedUserName)
                    break
        sUserId = tweet["author_id"]
        sUserName = FindUserNameById_v2(users, sUserId)
        sTweetUrl = "https://twitter.com/" + sUserName + "/status/" + tweet["id"]
        # Parse the twiff
        r = self.TwiffParser_v2(sTwiffText, tTweetDate, sTweetUrl, sQuoteURL)
        r["twiff_id"] = sTweetUrl.split("/")[5]
        if sQuoteURL != "":
            r["quote_id"] = sQuoteURL.split("/")[5]
        # Check for banned words
        if any(word in sTweetText.split() for word in self.BannedWords["single_words"]):
            r["response"] = "failed"
            r["errors"] = AddError_v2(r["errors"], "banned_word")
            r["twiff_id"] = None
            r["quote_id"] = None
        elif any(word in sTweetText for word in self.BannedWords["multi_words"]):
            r["response"] = "failed"
            r["errors"] = AddError_v2(r["errors"], "banned_word")
            r["twiff_id"] = None
            r["quote_id"] = None
        # Check for ignored users
        if self.CheckIgnoredUser(tweet["author_id"], users):
            r["errors"] = AddError_v2(r["errors"], "ignored_user")
            r["twiff_id"] = None
            r["quote_id"] = None
        if sTweetType == "Quoted":
            if self.CheckIgnoredUser(sQuotedUserId, users):
                r["errors"] = AddError_v2(r["errors"], "ignored_user")
                r["twiff_id"] = None
                r["quote_id"] = None
        r["tweettype"] = sTweetType
        return r

    def TwiffParser_v2(self, TwiffText, TweetDate, TweetURL, QuoteURL) -> dict:
        """
        # Let's see if we can extract twiff data from the tweet
        # Us machines need to account for the fact that humans make mistakes,
        # so let's see if we can work with whatever the human gave us.

            Args:
                TwiffText (String): Text extracted from the tweet containing only twiff data
                TweetDate (DateTime): Date and time of the twiff
                TweetURL (String): URL to the tweet containing the twiff
                QuoteURL (String): URL of the tweet qouted by the twiff, if no qoute then this field is ""

            Example::
                #>>> vars = {}
                #>>> result = TwiffParser_v2(**vars)
                #>>> log.info(result)

        """
        r = {"response": "failed",
             "tweettype": None,
             "twiff_id": None,
             "quote_id": None,
             "data": {"num_people": 0,
                      "created_at": "",
                      "organization": "",
                      "location": "",
                      "url": ""},
             "errors": []}
        if len(TwiffText) < 10:
            r["errors"] = AddError_v2(r["errors"], "twifftext_too_short")
            return r

        # let's assume the 6th character is a delimiter,
        # Unless that is a space, then check for a delimiter after the space, or numbers.
        i = 6
        while TwiffText[i:i + 1] == " " or TwiffText[i:i + 1].isnumeric() or TwiffText[i:i + 1].isalpha():
            i += 1
        sDelimiter = TwiffText[i:i + 1]
        TwiffText = TwiffText[6:]
        # remove the quote URL if needed
        if QuoteURL != "":
            TwiffText = TwiffText.replace(QuoteURL, "")
        # Also cut out when a new line is started
        if "\n" in TwiffText:
            TwiffText = TwiffText.split("\n")[0]
        if "https://t.co/" in TwiffText:
            TwiffText = TwiffText.split("https://t.co/")[0]
        # TwiffText is a string that only contains twiff data, can it contain useful information?
        # secondary check to see if continuing is useful
        if len(TwiffText) < 10:
            r["errors"] = AddError_v2(r["errors"], "twifftext_too_short")
            return r
        # Now we know the delimiter, create the datafields
        sDatafields = TwiffText.split(sDelimiter)
        # Clean up actions
        i = 0
        while i < len(sDatafields):
            sDatafields[i] = sDatafields[i].strip(" ()[]{}#\n")  # Sometime people use brackets :\
            i += 1
        # Let's try to get some results
        nPeople = 0  # Expected as parameter 0
        sOrganisation = ""  # Expected as parameter 1
        sCountry = ""  # Expected as parameter 2
        sState = ""  # Expected as parameter 3
        sCity = ""  # Expected as parameter 4
        tDate: datetime = None  # Expected as parameter 5
        sURL = ""  # Expected as parameter 6
        # But humans aren't perfect, so they'll probs mess up :)
        for sDatafield in sDatafields:
            if sDatafield == "":
                continue
            # If it's a number is must be the numer of people (0)
            if sDatafield.isnumeric() and nPeople == 0:  # 20220415 Added 0 check
                nPeople = int(sDatafield)
                continue
            # If it starts with a number, and is between 6 and 10 chars long, it must be the date(5)
            if sDatafield[0:2].isnumeric():
                bOK, tDate = TryParseDateOnly_v2(sDatafield)
                if not bOK:
                    tDate = None
                continue
            # The rest are text strings, we can only check for URLs
            if sDatafield.startswith("http"):
                sURL = sDatafield
                continue
            # Otherwise let's hope people used the right order
            if sOrganisation == "":
                sOrganisation = sDatafield
                continue
            if sCountry == "":
                sCountry = sDatafield
                continue
            if sState == "":
                sState = sDatafield
                continue
            if sCity == "":
                sCity = sDatafield
                continue
        # We now came out of a very long loop checking twiff data letter by letter
        # If we don't have a city, but do have a state, the state was probs omitted
        if sState != "" and sCity == "":
            sCity = sState
            sState = ""
        # If no date was found, use tweet date
        if tDate is None:
            tDate = datetime.datetime.strptime(TweetDate, "%Y-%m-%dT%H:%M:%S.000Z")
        if sURL == "":
            if QuoteURL == "":
                sURL = TweetURL
            else:
                sURL = QuoteURL

        # Clean up locations
        if "." in sCountry:
            sCountry = sCountry.split(".")[0]
        if "." in sState:
            sState = sState.split(".")[0]
        if "." in sCity:
            sCity = sCity.split(".")[0]

        # We now made the most of the data as we could, let's do some basic checks before reporting
        if len(sOrganisation) < 3 or len(sOrganisation) > 50 or "http" in sOrganisation:
            r["errors"] = AddError_v2(r["errors"], "no_org_found")
        if len(sCountry) < 2 or len(sCountry) > 35 or "http" in sCountry:
            r["errors"] = AddError_v2(r["errors"], "no_country_found")
        if len(sState) > 35 or "http" in sState:
            r["errors"] = AddError_v2(r["errors"], "no_state_found")
        if len(sCity) > 60 or "http" in sCity:
            r["errors"] = AddError_v2(r["errors"], "no_city_found")
        if nPeople == 0:
            r["errors"] = AddError_v2(r["errors"], "no_people_found")
        # Report back the results
        dParsed: dict
        sFullLocation = sCountry
        if sState != "":
            sFullLocation = sFullLocation + " " + sState
        sFullLocation = sFullLocation + " " + sCity
        if len(r["errors"]) > 0:
            r["response"] = "failed"
        else:
            r["response"] = "success"
        r["data"] = {"num_people": nPeople,
                     "created_at": tDate.strftime("%d-%m-%Y"),
                     "organization": sOrganisation,
                     "location": sFullLocation,
                     "url": sURL}
        return r

    def CheckIgnoredUser(self, UserID, users: dict) -> bool:
        """
        Check whether the user will be ignored

        Args:
            UserID (String): The user ID to search for
            users (dict): The user information to search in.

        Returns:
            Ignored (bool): True if the user should be ignored

        """

        if UserID in self.IgnoredUsers:
            return True
        else:
            # If not found by ID, find by handle
            sUserName = FindUserNameById_v2(users, UserID)
            sEntry = "x"
            for userdata in self.IgnoredUsers:
                if self.IgnoredUsers[userdata] == sUserName:
                    sEntry = userdata
            if sEntry != "x":
                del self.IgnoredUsers[sEntry]
                self.IgnoredUsers[UserID] = sUserName
                with open(Path("ignored_users.json"), 'w') as fp:
                    json.dump(self.IgnoredUsers, fp)
                return True
        return False


def FindUserNameById_v2(users: dict, userID):
    """
    Find a users name by its ID

    Args:
        users (list): The user information to search in.
        userID (String): The user ID to search for

    Returns:
        Username (String): The name of the user, None if no user was found

    """

    user: dict
    for user in users.values():
        if user["id"] == userID:
            return user["username"]


def FindUserIdByName_v2(users: dict, userName):
    """
    Find a users ID by its name

    Args:
        users (list): The user information to search in.
        userName (String): The user name to search for

    Returns:
        UserID (String): The ID of the user, None if no user was found

    """

    user: dict
    for user in users.values():
        if user["username"] == userName:
            return user["id"]


def AddError_v2(errors: [], newError: str) -> []:
    """
    Add error to error list

    Args:
        errors (list): List of current errors
        newError (String): The new error to add to the list

    Returns:
        errors (list): The new list of errors

    """

    if errors is None:
        errors = [newError]
    else:
        errors.append(newError)
    return errors


def TryParseDateOnly_v2(DateTimeString: str):
    """
    Parses 4 formats, year always 4 digits
    1 when / is used in the string American annotation is assumed
         1.1 Year first or month first: 2000/31/12 or 12/31/2000
    2 any other delimiter EU standard is assumed
         2.1 Year first or day first: 31-12-2000 or 2000-12-31

    Args:
        DateTimeString (String): The date time string to parse

    Returns:
        ParseResult (bool): True if parse is successful
        DateTime (datetime): The parsed date/time

    """

    tDate: datetime = datetime.datetime.now()
    # sDate = tDate.strftime("%d-%m-%Y")
    # First check if this has any chance of success
    if len(DateTimeString) != 10:
        return False, tDate
    # Is the year in the first place?
    if DateTimeString[4:5].isnumeric():
        # If so split by the char in 3rd place
        sNumbers = DateTimeString.split(DateTimeString[2:3])
        # is the delimiter a / (american style)
        if DateTimeString[2:3] == "/":
            # American style, convert to EU style, date first
            sDate = sNumbers[1] + "-" + sNumbers[0] + "-" + sNumbers[2]
        else:
            # No conversion needed, but make sure -'s are in, not any other delimiter
            sDate = sNumbers[0] + "-" + sNumbers[1] + "-" + sNumbers[2]
    else:
        # If not split by the char in 5th place
        sNumbers = DateTimeString.split(DateTimeString[4:5])
        # is the delimiter a / (american style)
        if DateTimeString[4:5] == "/":
            # American style, convert to EU style, date first
            sDate = sNumbers[1] + "-" + sNumbers[2] + "-" + sNumbers[0]
        else:
            # Rotate so year goes last
            sDate = sNumbers[2] + "-" + sNumbers[1] + "-" + sNumbers[0]
    tDate = datetime.datetime.strptime(sDate, "%d-%m-%Y")
    return True, tDate
