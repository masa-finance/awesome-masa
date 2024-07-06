import csv
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the API endpoint from environment variable
api_endpoint = os.getenv('MASA_NODE_URL', 'http://localhost:8080/api/v1/data/twitter/tweets/recent')
headers = {
    'accept': 'application/json',
    'Content-Type': 'application/json'
}

# Define the request body to get the latest 100 tweets from elonmusk
query = "(from:elonmusk)"

request_body = {
    "query": query,
    "count": 100
}

# Make the POST request
response = requests.post(api_endpoint, json=request_body, headers=headers, timeout=10)

# Check if the request was successful
if response.status_code == 200:
    response_data = response.json()  # Parse the JSON response

    # Prepare data for CSV
    tweets_data = []
    for tweet in response_data['data']:
        # Convert Unix timestamp to readable date (YYYY-MM-DD format)
        date = datetime.utcfromtimestamp(tweet['Timestamp']).strftime('%Y-%m-%d')
        text = tweet['Text']
        tweets_data.append([text, date])

    # Write data to a CSV file
    with open('data/elon_tweets.csv', 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['tweet', 'date'])  # Write headers
        writer.writerows(tweets_data)  # Write tweet data
else:
    print(f"Failed to fetch tweets: {response.status_code}")