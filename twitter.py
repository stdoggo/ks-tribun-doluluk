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
if result:
    if len(result) == 2:
        output, match_date = result
        AWAY = None
    else:
        output, match_date, AWAY = result
    print(output)
else:
    print("No data")

# Convert match date to date format
timezone = pytz.timezone("Europe/Istanbul")
match_date = timezone.localize(datetime.strptime(match_date, "%Y-%m-%d %H:%M"))

# Schedule tweets
def schedule_tweets():
    schedule.clear()
    current_date = datetime.now(timezone)
    remaining_days = (match_date - current_date).days

    if AWAY:
        # Away match
        tweet_hours = ["12:00", "20:00"]
        if remaining_days == 0:
            tweet_hours = [h for h in tweet_hours if h < match_hour]
            tweet_hours.append((match_date).strftime("%H:%M"))
    else:
        # Home match
        if remaining_days >= 4:
            # 4 or more days left
            tweet_hours = ["12:00", "20:00"]
            
        elif 0 <= remaining_days < 4:
            # 0-4 days left
            tweet_hours = ["12:00", "16:00", "20:00"]
            
        elif remaining_days == 0:
            # Match day
            match_hour = match_date.strftime("%H:%M")
            tweet_hours = [h for h in ["10:00", "12:00", "14:00", "16:00", "18:00"] if h < match_hour]
            tweet_hours.append((match_date).strftime("%H:%M"))
        else:
            # After the match
            tweet_hours = ["12:00"]
    
    if not result:
        # No match found
        tweet_hours = ["12:00"]

    for time in tweet_hours:
        schedule.every().day.at(time).do(post_tweet)

# Post the tweet
def post_tweet():
    try:
        print("Twit atılıyor...")
        client.create_tweet(text=output)
    except Exception as e:
        print(f"Twit atılırken hata: {e}")

# Main loop
post_tweet() # debug
schedule_tweets()
while True:
    schedule.run_pending()
    time.sleep(60)
    

