import os
import tweepy
from dotenv import load_dotenv
from main import main

# .env file
load_dotenv(dotenv_path='../ks-tribun-doluluk/keys.env')

# Twitter credentials
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
bearer_token = os.getenv("BEARER_TOKEN")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

# Twitter clients
client = tweepy.Client(bearer_token, api_key, api_secret, access_token, access_token_secret)
auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
api = tweepy.API(auth)

# Run main script and get the output
output = main()
tweet = client.create_tweet(text=output)

##### oto dm paralı olmuş çalışmıyor
# tweet_id = tweet.data["id"]
# user_id = "user_id"
# tweet_url = f"https://x.com/KSTribunDoluluk/status/{tweet_id}"
# api.send_direct_message(user_id, tweet_url)
