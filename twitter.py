import os
import time
import pytz
import tweepy
import schedule
from dotenv import load_dotenv
from main import main
from datetime import datetime

# Load .env
load_dotenv(dotenv_path='keys.env')

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

# Get output and match date from the main script
result = main()
output = result

# Post the tweet
def post_tweet():
    try:
        print("Twit atılıyor...")
        client.create_tweet(text=output)
    except Exception as e:
        print(f"Twit atılırken hata: {e}")

# Main loop
post_tweet() # debug
    

