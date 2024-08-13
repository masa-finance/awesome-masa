"""
This script fetches tweets based on a specified query and date range, and saves the fetched tweets to a local directory.
It supports resuming from the last known state in case of interruptions. The script uses a configuration file 
(tweet_fetcher_config.yaml) to set various parameters such as API endpoint, query, date range, and retry settings.

Configuration:
- The configuration file 'tweet_fetcher_config.yaml' includes settings for API endpoint, headers, query, 
  tweets per request, date range, data directory, retry and request delays, maximum retries, request timeout, 
  and logging settings.

Functions:
- load_config: Loads the configuration from the YAML file.
- save_state: Saves the current state, API call count, records fetched, and a sample of tweets to a JSON file.
- load_state: Loads the last known state from a JSON file.
- fetch_tweets: Main function to fetch tweets based on the configuration and save them.

The script is designed to be run as a standalone program.
"""

import requests
import os
import yaml
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
import logging
import json
from tweet_service import setup_logging, ensure_data_directory, save_tweets, create_tweet_query, load_existing_tweets
from requests.exceptions import ReadTimeout, ConnectionError, RequestException


def load_config():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(dir_path, 'tweet_fetcher_config.yaml')
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def save_state(state, api_calls_count, records_fetched, all_tweets):
    state_data = {
        'last_known_state': state,
        'api_calls_count': api_calls_count,
        'records_fetched': records_fetched,
        'all_tweets_sample': all_tweets[:10]
    }
    with open('last_known_state_detailed.json', 'w') as f:
        json.dump(state_data, f, indent=4)

def load_state():
    try:
        with open('last_known_state_detailed.json', 'r') as f:
            return json.load(f).get('last_known_state', {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def fetch_tweets(config):
    api_calls_count = 0
    records_fetched = 0
    all_tweets = load_existing_tweets(config['data_directory'], config['query'])

    start_date = datetime.strptime(config['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(config['end_date'], '%Y-%m-%d').date()
    days_per_iteration = config['days_per_iteration']

    ensure_data_directory(config['data_directory'])

    logging.info("Starting to fetch tweets...")

    last_known_state = load_state()
    if last_known_state:
        current_date = datetime.strptime(last_known_state['current_date'], '%Y-%m-%d').date()
        logging.info(f"Resuming from {current_date}")
    else:
        current_date = end_date

    while current_date >= start_date:
        success = False
        attempts = 0
        while not success and attempts < config['max_retries']:
            iteration_start_date = current_date - timedelta(days=days_per_iteration)
            day_before = max(iteration_start_date, start_date - timedelta(days=1))

            query = create_tweet_query(config['query'], day_before, current_date)
            request_body = {"query": query, "count": config['tweets_per_request']}

            try:
                response = requests.post(config['api_endpoint'], 
                                         json=request_body, 
                                         headers=config['headers'], 
                                         timeout=config['request_timeout'])
                api_calls_count += 1

                if response.status_code == 200:
                    response_data = response.json()
                    if response_data and 'data' in response_data and response_data['data'] is not None:
                        new_tweets = response_data['data']
                        all_tweets.extend(new_tweets)
                        num_tweets = len(new_tweets)
                        records_fetched += num_tweets
                        logging.info(f"Fetched {num_tweets} tweets for {current_date.strftime('%Y-%m-%d')} to {day_before.strftime('%Y-%m-%d')}.")
                        success = True
                        
                        save_tweets(all_tweets, config['data_directory'], config['query'])
                        save_state({'current_date': current_date.strftime('%Y-%m-%d')}, api_calls_count, records_fetched, all_tweets)
                    else:
                        logging.warning(f"No tweets fetched for {current_date.strftime('%Y-%m-%d')} to {day_before.strftime('%Y-%m-%d')}. Rate limited, pausing before retrying...")
                        time.sleep(config['retry_delay'])
                        attempts += 1
                elif response.status_code == 504:
                    logging.warning(f"Received 504 error for {current_date.strftime('%Y-%m-%d')} to {day_before.strftime('%Y-%m-%d')}. Pausing before retrying...")
                    time.sleep(config['retry_delay'])
                    attempts += 1
                else:
                    logging.error(f"Failed to fetch tweets for {current_date.strftime('%Y-%m-%d')} to {day_before.strftime('%Y-%m-%d')}: {response.status_code}")
                    break

            except ReadTimeout:
                logging.warning(f"Read timeout occurred for {current_date.strftime('%Y-%m-%d')} to {day_before.strftime('%Y-%m-%d')}. Retrying...")
                time.sleep(config['retry_delay'])
                attempts += 1
            except ConnectionError:
                logging.warning(f"Connection error occurred for {current_date.strftime('%Y-%m-%d')} to {day_before.strftime('%Y-%m-%d')}. Retrying...")
                time.sleep(config['retry_delay'])
                attempts += 1
            except RequestException as e:
                logging.error(f"An error occurred while fetching tweets for {current_date.strftime('%Y-%m-%d')} to {day_before.strftime('%Y-%m-%d')}: {str(e)}")
                break

        if not success:
            logging.error(f"Failed to fetch tweets for {current_date.strftime('%Y-%m-%d')} to {day_before.strftime('%Y-%m-%d')} after {attempts} attempts.")

        current_date -= timedelta(days=days_per_iteration)

        time.sleep(config['request_delay'])

    logging.info(f"Operation completed. Total API calls made: {api_calls_count}. Total records fetched: {records_fetched}")

if __name__ == "__main__":
    load_dotenv()
    config = load_config()
    setup_logging(config['log_level'], config['log_format'])
    fetch_tweets(config)