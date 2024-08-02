# Getting Started with the Tweet Fetcher

## Introduction
The Tweet Fetcher is a Python script designed for developers to fetch tweets from a specified Twitter account within a given date range. This README provides instructions on setting up and using the Tweet Fetcher.

## Prerequisites
- Conda installed on your system.
- An environment set up using the provided `environment.yml` file. To set up the environment, run:
  ```bash
  conda env create -f environment.yml
  ```
  Activate the environment with:
  ```bash
  conda activate awesome-masa
  ```

## Configuration
Before running the script, you need to configure it to specify the API endpoint, query parameters, and other settings.

1. **API Settings**: Specify the API endpoint and headers for the request.
2. **Query Settings**: Define the query for fetching tweets, including the Twitter account and the number of tweets per request.
3. **Date Range**: Set the `start_date` and `end_date` for the period from which you want to fetch tweets.
4. **Iteration Settings**: Adjust `days_per_iteration` to control how many days' worth of tweets are fetched per iteration within the date range.
5. **File and Logging Settings**: Specify the directory for saving fetched tweets and configure logging preferences.

Refer to the configuration file section for more details:

```1:25:examples/tweets/tweet_fetcher_config.yaml
# API settings
api_endpoint: 'http://localhost:8080/api/v1/data/twitter/tweets/recent'
headers:
  accept: 'application/json'
  Content-Type: 'application/json'

# Query settings
query: 'from:milesdeutscher'
tweets_per_request: 100

# Add start_date and end_date
start_date: '2023-07-24'
end_date: '2024-07-24'
days_per_iteration: 10

# File settings
data_directory: 'data'

# Timing settings
retry_delay: 960  # 16 minutes in seconds
request_delay: 15  # 15 seconds between requests

# Logging settings
log_level: 'INFO'
log_format: '%(asctime)s - %(levelname)s - %(message)s'
```


## Running the Script
To fetch tweets, follow these steps:

1. Navigate to the script's directory in your terminal.
2. Run the script using Python:
   ```bash
   python tweet_fetcher.py
   ```

## How It Works
The script performs the following steps:

1. Loads the configuration from `tweet_fetcher_config.yaml`.
2. Fetches tweets based on the specified query and date range.
3. Saves the fetched tweets in the specified directory as a JSON file.

Refer to the service module for more details on the functions used:

```1:23:examples/tweets/tweet_service.py
import json
import logging
import os
import time
from datetime import datetime

def setup_logging(log_level, log_format):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    logging.basicConfig(level=numeric_level, format=log_format)

def ensure_data_directory(directory):
    os.makedirs(directory, exist_ok=True)

def save_all_tweets(tweets, data_directory):
    filename = f'{data_directory}/all_tweets_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json'
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(tweets, file, ensure_ascii=False, indent=2)
    logging.info(f"All tweets saved to {filename}")

def create_tweet_query(hashtag, start_date, end_date):
    return f"({hashtag} until:{end_date.strftime('%Y-%m-%d')} since:{start_date.strftime('%Y-%m-%d')})"
```


## Output
The fetched tweets are saved in the `data_directory` specified in the configuration file. Each file is named with a timestamp to ensure uniqueness.

## Logging
The script logs its progress and any errors encountered during execution. You can adjust the log level and format in the configuration file to suit your needs.

## Customization
You can customize the script by modifying the configuration file or extending the Python scripts to add new functionality or adjust existing features.

For any issues or further assistance, please refer to the inline documentation within the codebase.