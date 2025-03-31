import os
import requests
import pytz
import time
import tweepy
from tweepy.errors import TooManyRequests
from dotenv import load_dotenv
from main import main
from datetime import datetime

# Date of the data
timezone = pytz.timezone("Europe/Istanbul")
current_date = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")

# .env file
load_dotenv(dotenv_path='../ks-tribun-doluluk/keys.env')

# Twitter credentials
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
bearer_token = os.getenv("BEARER_TOKEN")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

# API key for output.txt
github_token = os.getenv("GITHUB_TOKEN")

# Twitter clients
client = tweepy.Client(bearer_token, api_key, api_secret, access_token, access_token_secret)
auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
api = tweepy.API(auth)

# Run main script and get the output
output = main()
tweet = client.create_tweet(text=output)

# Upload output.txt
filename = "output.txt"
description = f"Blok doluluk durumu ({current_date})"
public = True

with open(filename, "r", encoding="utf-8") as f:
    content = f.read()

payload = {
    "description": description,
    "public": public,
    "files": {
        filename: {
            "content": content
        }
    }
}

response = requests.post(
    "https://api.github.com/gists",
    json=payload,
    headers={
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json"
    }
)

# Shorten github url
def shorten_url(long_url):
    response = requests.get(f"http://tinyurl.com/api-create.php?url={long_url}")
    if response.status_code == 200:
        return response.text
    return None

# Tweet url as a reply
if response.status_code == 201:
    gist_data = response.json()
    gist_url = gist_data["html_url"]
    raw_url = list(gist_data["files"].values())[0]["raw_url"]
    short_url = shorten_url(raw_url)
    try:
        if short_url:
            original_tweet_id = tweet.data["id"]
            reply_text = f"Blok doluluk oranları için:\n{short_url}"
            client.create_tweet(text=reply_text, in_reply_to_tweet_id=original_tweet_id)
    except Exception as e:
        print("URL paylaşılırken hata:", e)
else:
    pass

##### oto dm paralı olmuş çalışmıyor
# tweet_id = tweet.data["id"]
# user_id = "user_id"
# tweet_url = f"https://x.com/KSTribunDoluluk/status/{tweet_id}"
# api.send_direct_message(user_id, tweet_url)
