import os
from dotenv import load_dotenv
import tweepy # type: ignore
from main import main

load_dotenv(dotenv_path='../ks-tribun-doluluk/keys.env')

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
bearer_token = os.getenv("BEARER_TOKEN")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET") 

client = tweepy.Client(bearer_token, api_key, api_secret, access_token, access_token_secret)
auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
api = tweepy.API(auth)

output = main()
user_id = "1838289631013671158"

tweet = client.create_tweet(text=output)

tweet_id = tweet.id
tweet_url = f"https://x.com/KSTribunDoluluk/status/{tweet_id}"
api.send_direct_message(user_id, tweet_url)