"""
TODO:
    Handle not retweeting already re-tweeted tweets.
    Handle not replying to already replied-to tweets.

"""
import os
import sys
import json
import tweepy
import logging
import datetime

from typing import *
from argparse import ArgumentParser, Namespace

#from . import load_module
from importlib import import_module

def load_module(config, module, *args, **kwargs):
    if f"{module}" in config: 
        module_config = config[f"{module}"]
        func_module = import_module(module_config["module"])
        func_call = getattr(func_module, module_config["call"])
        func_kwargs = {**kwargs, **module_config["config"]} if "config" in module_config else {**kwargs}
        return func_call(*args, **func_kwargs)
    else:
        return None


log = logging.getLogger(__name__)

def search(client:Any, cursor:str, query:str, max_requests:Optional[int]=10) -> Tuple[Dict, Dict, list, Dict]:
    """ Search Tweets
    
        Authentication methods supported: OAuth 2.0 Authorization Code with PKCE
        Rate limit: 450 requests per 15-minute window shared among all users of your app
    
        Args:
            client (): 
            cursor (str):
            query (str):
            max_requests (Optional[int]=100): 
            
        Returns:
            tweets (Dict): 
            users (Dict): 
            errors (list): 
            metadata (Dict): 
            
        Example::
            >>>
            >>>
            >>>
            
    """
    tweets, users, errors, metadata = {}, {}, [], {}
    
    # Prepare cursors for retrieving tweets.
    from .utils.cursor import Cursor
    new_cursor = Cursor()
    old_cursor = Cursor(cursor)
    
    # Search for tweets
    responses = client.search_recent_tweets(query=query, 
                                            expansions=['author_id', 'entities.mentions.username', 'geo.place_id', 'in_reply_to_user_id', 'referenced_tweets.id', 'referenced_tweets.id.author_id'],
                                            max_results=max_requests, 
                                            place_fields=['country', 'country_code', 'full_name', 'geo', 'id', 'name', 'place_type'],
                                            since_id=old_cursor._newest_id(),
                                            tweet_fields=['author_id', 'conversation_id', 'created_at', 'entities', 'geo', 'id', 'in_reply_to_user_id', 'lang', 'referenced_tweets', 'reply_settings', 'source', 'text', 'withheld'],
                                            until_id=new_cursor._oldest_id(),
                                            user_fields=['created_at', 'description', 'entities', 'id', 'location', 'name', 'url', 'username', 'verified', 'withheld']
                                           )

    # Process tweet data
    if 'data' in responses:
        for tweet in responses['data']:
            tweets[tweet['id']] = tweet
    
    # Process user data
    if 'includes' in responses:
        for user in responses['includes']['users']:
            users[user['id']] = user

    # Process error data
    if 'errors' in responses:
        for error in responses['errors']:
            errors.append(error)

    # Process metadata data
    metadata = responses['meta']

    # Update cursor
    if metadata['result_count']:
        new_cursor._update(metadata['oldest_id'], metadata['newest_id'])
        new_cursor._dump(cursor)
    
    log.info(f"Retrieved {len(tweets)} tweets and {len(users)} associated users. Encountered {len(errors)} errors.")
            
    return tweets, users, errors, metadata
                       
    
def parse(tweets:Dict, users:Dict, parser:Callable) -> Dict:
    """ Handles parsing of tweets using the provided tweet parsing method.
    
        NOTE: 
            Contract for returned parsed tweet should be a dictionary containing the necessary key, value pairs that
            the response_generator can use to determine an approriate response from. 
    
        Args:
            tweets (Dict):
            parser (Callable):
            
        Returns:
            parsed_tweets (Dict): Dictionary containing parsed tweets. Key=tweet_id, Values=...
            
        Example::
            >>> x
            >>> y
            
    """
    parsed_tweets = {}
    for idx, (id_str, tweet) in enumerate(tweets.items()):
        parsed_tweets[id_str] = parser(tweet, users)
    log.info(f"Successfully parsed {len([None for val in parsed_tweets.values() if val is not None])} tweets out of {len(tweets)}.")
        
    return parsed_tweets


def record(tweets: Dict, api_key: str, recorder: Callable) -> Dict:
    """ Handles recording of tweets using the provided recording method.

        NOTE:
            Contract: the parsed tweet key, value pairs will be used and updated accoring to achieved results so that
            the response_generator can use this to determine an approriate response from.

        Args:
            tweets (Dict): The parsed tweets
            api_key (str): API key for the Google maps API
            recorder (Callable): Recorder module

        Returns:
            parsed_tweets (Dict): Dictionary containing parsed tweets.

        Example::
            >>> x
            >>> y

    """
    parsed_tweets = {}
    success = 0
    for idx, (id_str, tweet) in enumerate(tweets.items()):
        try:
            parsed_tweets[id_str] = recorder(tweet, api_key)
            success += 1
        except:
            log.exception(f"Could not record {id_str}")
            parsed_tweets[id_str] = tweet
    log.info(
        f"Successfully recorded {success} tweets out of {len(tweets)}.")

    return parsed_tweets


def like(client:Any, parsed_tweets:Dict, condition:Callable, max_requests:Optional[int]=10) -> None:
    """ Likes tweets using associated tweet id.

        Using max_likes may be necessary depending on whether you can afford to respect wait limits for all retrieved tweets.

        Authentication methods supported: OAuth 2.0 Authorization Code with PKCE
        Rate limit: 50 requests per 15-minute window per each authenticated user

        Args:
            X

        Returns:
            X

        Example::
            X

    """
    if max_requests:
        success = 0
        for idx, (id_str, parsed_tweet) in enumerate(parsed_tweets.items()):
            if parsed_tweet["twiff_id"] is not None:
                # if condition(tweet): // Removed, parser handles the conditions
                client.like(parsed_tweet["twiff_id"])
                success += 1
            if parsed_tweet["quote_id"] is not None:
                client.like(parsed_tweet["quote_id"])
                success += 1
            if success >= max_requests: break
    log.info(f"Liked {success} tweets.")


def retweet(client:Any, parsed_tweets:Dict, condition:Callable, max_requests:Optional[int]=10) -> None:
    """ Retweets tweets using associated tweet id.

        Using max_retweets may be necessary depending on whether you can afford to respect wait limits for all retrieved tweets.

        Authentication methods supported: OAuth 2.0 Authorization Code with PKCE
        Rate limit: 50 requests per 15-minute window per each authenticated user

        Args:
            X

        Returns:
            X

        Example:
            X

    """
    if max_requests:
        success = 0
        for idx, (id_str, parsed_tweet) in enumerate(parsed_tweets.items()):
            if parsed_tweet["twiff_id"] is not None:
                # if condition(parsed_tweet) is not None: // Removed, parser handles the conditions
                client.retweet(parsed_tweet["twiff_id"])
                success += 1
            if parsed_tweet["quote_id"] is not None:
                client.retweet(parsed_tweet["quote_id"])
                success += 1
            if success >= max_requests: break
    log.info(f"Retweeted {success} tweets.")
            
    
def reply(client:Any, parsed_tweets:Dict, generator:Callable, max_requests:Optional[int]=10) -> None:
    """ Replies to the author of the parsed tweet as dictated by the provided response_generator.
        
        Authentication methods supported: OAuth 2.0 Authorization Code with PKCE
        Rate limit: 200 requests per 15-minute window per each authenticated user
    
    
        Args:
            client (tweepy.Client): Registered and X client.
            parsed_tweets (Dict): Parsed tweet data in dictionary format.
                Key (str): Unique ID corresponding to the tweet.
                Value (Dict):
                    num_people (int):
                    created_at (str):
                    organization (str):
                    location (str): 
            response_generator (Callable): Callable function to generate response based on parsed tweet data.
            
        Returns:
            None
            
        Example::
            >>> tweets = search(...)
            >>> parsed_tweets = twiff.utils.parse.parse_tweets(tweets)
            >>> reply(client, parsed_tweets, ...) # ...
            
    """
    # TODO: Replying to tweets needs persistent memory of replied-to tweets, can't get this from API easily to use filesystem.
    from pathlib import Path
    path = "/home/deploy/gamechanger/twiff/output/tweets"
    ids = [p.name.split('.')[0] for p in Path(path).glob("*.json")] if Path(path).exists() else []
    
    if max_requests:
        success = 0
        for idx, (id_str, parsed_tweet) in enumerate(parsed_tweets.items()):
            if id_str not in ids:
                response = generator(parsed_tweet)
                if response is not None:
                    if response != "":
                        try:
                            client.create_tweet(in_reply_to_tweet_id=id_str, text=response)
                            success += 1
                        except:
                            log.exception("Could not reply to " + id_str + ", intended reply was: " + response)
            else:
                log.info(f"Tweet ID ({id_str}) has already been processed.")
            if success >= max_requests: break
    log.info(f"Replied to {success} tweets.")


def run(args:Namespace) -> None:
    '''
    
    '''
    # Log
    log.info(f"Search Arguments: {args}")
    
    # Configuration
    with open(args.config, 'r') as fp:
        config = json.load(fp)
    
    # API Keys
    if os.getenv("TWITTER_API_KEYS_FILE", None) is not None:
        keys = {}
        with open(os.getenv("TWITTER_API_KEYS_FILE", None), "r") as fp:
            for line in fp.readlines():
                key, val = line.split("=")
                keys[key] = val.strip()
    else:
        raise ValueError(f"No API_KEYS file provided in environment variables. User should implement a method here to read keys from args.")
    
    # Initialise tweepy client
    from tweepy import Client
    client = Client(
        keys['BEARER_TOKEN'], 
        keys['API_KEY'], keys['API_KEY_SECRET'], 
        keys['ACCESS_TOKEN'], keys['ACCESS_TOKEN_SECRET'], 
        return_type=dict, wait_on_rate_limit=True
    )
    log.info(f"User Agent: {client.user_agent}")
    
    # Print Authenticated User
    user = client.get_user(username="twiff_bot")['data']
    log.info(f"Authenticated User: [ {user['name']} ] {user['username']} (ID={user['id']})")
    
    # Perform search using provided query.
    tweets, users, errors, metadata = search(client=client, max_requests=args.max_requests, **config['search']['config'])
       
    # Attempt to parse tweets using provided method: parse according to pre-determined format
    parsed_tweets = parse(tweets=tweets, users=users, parser=load_module(config, "parser"))

    # Try to record the parsed tweets, adjust likes, retweets and responses accordingly
    parsed_tweets = record(tweets=parsed_tweets, api_key=keys['GMAPS_SECRET'], recorder=load_module(config, "recorder"))

    # Like retrieved tweets: like parsed tweets
    like(client=client, parsed_tweets=parsed_tweets, condition=load_module(config, "like-condition"), max_requests=args.max_requests)

    # Retweet retrieved tweets: retweet parsed tweets
    retweet(client=client, parsed_tweets=parsed_tweets, condition=load_module(config, "retweet-condition"), max_requests=args.max_requests)
    
    # Reply to parsed tweets using generated response: reply to all tweets with different responses
    reply(client=client, parsed_tweets=parsed_tweets, generator=load_module(config, "reply-generator"), max_requests=args.max_requests)
    
    # Export/dump data to disk for longer-term storage.
    load_module(config, "exporter", data={id_str:tweet for (id_str, tweet) in tweets.items()}, subdir="tweets")
    load_module(config, "exporter", data={id_str:user for (id_str, user) in users.items()}, subdir="users")
    load_module(config, "exporter", data={id_str:data for (id_str, data) in parsed_tweets.items()}, subdir="parsed-tweets")
    
    
def get_arg_parser() -> ArgumentParser:
    '''
    Argument Parser
    '''
    import argparse
    parser = argparse.ArgumentParser(description='Twitter Search', 
                                     epilog='Please contact Sam for further help.')    
    parser.add_argument('--config', type=str,
                        help='Configuration file for running the job.') 
    parser.add_argument('--max_requests', type=int, default=None,
                        help='Maximum number of requests.')   
    return parser


def parse_args(args:Optional[Dict[str,Any]]={}) -> Namespace:
    '''
    Parse Arguments
    '''
    parser = get_arg_parser()
    parser.set_defaults(**args)
    args = parser.parse_args([])
    return args
    

def main(args:Optional[Dict[str,Any]]={}) -> None:
    '''
    Entry point.
    '''
    args = parse_args(args)
    run(args)
    
    
if __name__=='__main__':
    main()
