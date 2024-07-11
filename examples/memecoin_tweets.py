import csv
import os
import requests
import re
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from html import unescape
import logging
import time

# Setup basic configuration for logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load environment variables
load_dotenv()

# Define the API endpoint from environment variable
api_endpoint = os.getenv(
    "MASA_NODE_URL", "http://localhost:8080/api/v1/data/twitter/tweets/recent"
)
headers = {"accept": "application/json", "Content-Type": "application/json"}


# Function to clean tweet text
def clean_text(text):
    text = unescape(text)
    text = re.sub(r"https?:\/\/\S+", "", text)
    text = text.replace("\n", " ").replace("\r", " ")
    return text.strip()


# Prepare data for CSV
tweets_data = []
api_calls_count = 0
records_fetched = 0

# Define the date range for the period
end_date = datetime.now().date()
start_date = end_date - timedelta(days=1)

logging.info("Starting to fetch tweets...")

# Iterate from today backwards through the date range, day by day
current_date = end_date
while current_date >= start_date:
    success = False
    attempts = 0
    while not success and attempts < 3:
        day_before = current_date - timedelta(days=1)
        query = f"(#memecoin until:{current_date.strftime('%Y-%m-%d')} since:{day_before.strftime('%Y-%m-%d')})"
        request_body = {"query": query, "count": 100}

        response = requests.post(
            api_endpoint, json=request_body, headers=headers, timeout=10
        )
        api_calls_count += 1

        if response.status_code == 200:
            response_data = response.json()
            if (
                response_data
                and "data" in response_data
                and response_data["data"] is not None
            ):
                num_tweets = len(response_data["data"])
                records_fetched += num_tweets
                for tweet in response_data["data"]:
                    zulu_time = datetime.fromtimestamp(
                        tweet["Timestamp"], timezone.utc
                    ).strftime("%Y-%m-%dT%H:%M:%SZ")
                    text = clean_text(tweet["Text"])
                    tweets_data.append([text, zulu_time])
                logging.info(
                    f"Fetched {num_tweets} tweets for {current_date.strftime('%Y-%m-%d')}."
                )
                success = True
            else:
                logging.warning(
                    f"No tweets fetched for {current_date.strftime('%Y-%m-%d')}. Rate limited, pausing before retrying..."
                )
                time.sleep(960)  # Wait for 16 minutes before retrying
                attempts += 1
        else:
            logging.error(
                f"Failed to fetch tweets for {day_before.strftime('%Y-%m-%d')}: {response.status_code}"
            )
            break  # Exit the retry loop on hard failure

        if not success:
            logging.error(
                f"Failed to fetch tweets for {current_date.strftime('%Y-%m-%d')} after {attempts} attempts."
            )

    current_date = day_before
    time.sleep(15)

logging.info(
    f"Operation completed. Total API calls made: {api_calls_count}. Total records fetched: {records_fetched}."
)

# Write data to a CSV file
with open("data/memecoin_tweets.csv", "w", encoding="utf-8", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["tweet", "datetime"])
    writer.writerows(tweets_data)
    logging.info(f"Total records saved: {len(tweets_data)}")
