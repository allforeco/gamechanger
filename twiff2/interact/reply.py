import json
import re
import logging
from pathlib import Path

from typing import *

from abc import ABC, abstractmethod

log = logging.getLogger(__name__)


class ReplyGenerator(ABC):
    """ ...
    """

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        with open(self.path, 'r') as fp:
            self.responses = json.load(fp)

    @abstractmethod
    def __call__(self, parsed_tweet: Dict) -> str:
        """ Generate reponse based on parsed_tweet.

            Args:
                parsed_tweet (Dict): Parsed tweet
                    response (str): Type of response suggested.
                    data (Dict): Parsed data.

            Returns:
                response (str): Response text for the reply tweet.

            Example::
                >>> if parsed_tweet['response']=='success':
                        return self.responses['tweet-parse-success']
                    else:
                        return self.responses['tweet-parse-failed']
        """
        pass


class T4FReplyGenerator(ReplyGenerator):

    def __init__(self, path: str) -> None:
        '''
        Initialise the ReplyGenerator instance.
        '''
        super(T4FReplyGenerator, self).__init__(path)

    def __call__(self, parsed_tweet: Dict) -> str:
        """ Generate response based on parsed_tweet.

            Args:
                parsed_tweet (Dict): Parsed tweet
                    response (str): Type of response suggested.
                    data (Dict): Parsed data.

            Returns:
                response (str): Response text for the reply tweet.

        NOTES:
        --> Some Twitter rules: <--
        1: Max 280 chars in a tweet
        2: Any char counts, except for URLS and emoji's
        2a: A URL counts as 22 chars
        2b: An emoji counts as 2 chars
        """

        # Find the correct response
        # 1: Create the response type string based on results
        if parsed_tweet["twiff_id"]:
            sResponseType = "tweet-parse-" + parsed_tweet["response"]
            sPerson = "people"
            if parsed_tweet["response"] == "success":
                if "tweettype" in parsed_tweet:
                    sResponseType = sResponseType + "-" + parsed_tweet["tweettype"]
                    if parsed_tweet["data"]["num_people"] == 1:
                        sPerson = "person"
            else:
                if "errors" in parsed_tweet:
                    if parsed_tweet["errors"] is not None:
                        sResponseType = sResponseType + "-" + parsed_tweet["errors"][0]
            # 2: Create the response
            sResponse = self.responses[sResponseType].format(parsed_tweet["data"]["num_people"], sPerson,
                                    parsed_tweet["data"]["location"],
                                    parsed_tweet["data"]["organization"],
                                    parsed_tweet["data"]["url"])
            urls = re.findall("(?P<url>https?://[^\s]+)", sResponse)
            nTextLength = len(sResponse)
            for url in urls:
                nTextLength = (nTextLength - len(url)) + 22
            if nTextLength > 280:
                sResponseType = sResponseType + "-short"
                sResponse = self.responses[sResponseType].format(parsed_tweet["data"]["num_people"],
                                                             sPerson,
                                                             parsed_tweet["data"]["location"],
                                                             parsed_tweet["data"]["organization"],
                                                             parsed_tweet["data"]["url"])
            return sResponse
        else:
            return ""
