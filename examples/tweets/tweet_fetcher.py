import requests
import yaml
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
import logging
from tweet_service import setup_logging, ensure_data_directory, save_tweet_response, create_tweet_query

def load_config():
    with open('tweet_fetcher_config.yaml', 'r') as file:
        return yaml.safe_load(file)

def fetch_tweets(config):
    api_calls_count = 0
    records_fetched = 0

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=config['days_to_fetch'])

    ensure_data_directory(config['data_directory'])

    logging.info("Starting to fetch tweets...")

    current_date = end_date
    while current_date >= start_date:
        success = False
        attempts = 0
        while not success and attempts < 3:
            day_before = current_date - timedelta(days=1)
            query = create_tweet_query(config['query_hashtag'], day_before, current_date)
            request_body = {"query": query, "count": config['tweets_per_request']}

            response = requests.post(config['api_endpoint'], json=request_body, headers=config['headers'], timeout=60)
            api_calls_count += 1

            if response.status_code == 200:
                response_data = response.json()
                save_tweet_response(response_data, current_date, config['data_directory'])
                if response_data and 'data' in response_data and response_data['data'] is not None:
                    num_tweets = len(response_data['data'])
                    records_fetched += num_tweets
                    logging.info(f"Fetched and saved {num_tweets} tweets for {current_date.strftime('%Y-%m-%d')}.")
                    success = True
                else:
                    logging.warning(f"No tweets fetched for {current_date.strftime('%Y-%m-%d')}. Rate limited, pausing before retrying...")
                    time.sleep(config['retry_delay'])
                    attempts += 1
            else:
                logging.error(f"Failed to fetch tweets for {day_before.strftime('%Y-%m-%d')}: {response.status_code}")
                break

        if not success:
            logging.error(f"Failed to fetch tweets for {current_date.strftime('%Y-%m-%d')} after {attempts} attempts.")

        current_date = day_before
        time.sleep(config['request_delay'])

    logging.info(f"Operation completed. Total API calls made: {api_calls_count}. Total records fetched: {records_fetched}.")

if __name__ == "__main__":
    load_dotenv()
    config = load_config()
    setup_logging(config['log_level'], config['log_format'])
    fetch_tweets(config)