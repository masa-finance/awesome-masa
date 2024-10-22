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
from loguru import logger
import sys
import json
from tweet_service import setup_logging, ensure_data_directory, save_tweets, create_tweet_query, load_existing_tweets
from requests.exceptions import ReadTimeout, ConnectionError, RequestException
from loguru import logger
import concurrent.futures
from functools import partial
from statistics import mean


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



class NoWorkersAvailableError(Exception):
    pass



class TweetStats:
    def __init__(self):
        self.total_tweets = 0
        self.response_times = []
        self.start_time = time.time()
        self.unique_workers = set()

    def update(self, new_tweets, response_time, worker_id):
        self.total_tweets += new_tweets
        self.response_times.append(response_time)
        self.unique_workers.add(worker_id)

    def get_stats(self):
        elapsed_time = time.time() - self.start_time
        avg_response_time = mean(self.response_times) if self.response_times else 0
        tweets_per_minute = (self.total_tweets / elapsed_time) * 60 if elapsed_time > 0 else 0
        return self.total_tweets, avg_response_time, tweets_per_minute, len(self.unique_workers)

tweet_stats = TweetStats()

def fetch_tweets_for_date_range(config, start_date, end_date):
    api_calls_count = 0
    records_fetched = 0
    all_tweets = load_existing_tweets(config['data_directory'], config['query'])

    while start_date <= end_date:
        iteration_end_date = end_date
        iteration_start_date = max(start_date, end_date - timedelta(days=config['days_per_iteration']))
        
        query = create_tweet_query(config['query'], iteration_start_date, iteration_end_date)
        request_body = {"query": query, "count": config['tweets_per_request']}

        try:
            logger.debug(f"Sending request for {iteration_start_date.strftime('%Y-%m-%d')} to {iteration_end_date.strftime('%Y-%m-%d')}")
            logger.debug(f"Request body: {request_body}")
            
            start_time = time.time()
            response = requests.post(config['api_endpoint'], 
                                     json=request_body, 
                                     headers=config['headers'], 
                                     timeout=config['request_timeout'])
            end_time = time.time()
            response_time = end_time - start_time
            
            api_calls_count += 1

            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response content: {response.text[:1000]}...")  # Log first 1000 characters of response

            response_data = response.json()

            if response.status_code == 200:
                if response_data == {"Error": {}, "Tweet": None}:
                    logger.warning(f"Received an empty response for {iteration_start_date.strftime('%Y-%m-%d')} to {iteration_end_date.strftime('%Y-%m-%d')}. Waiting {config['empty_response_delay']} seconds before retrying...")
                    time.sleep(config['empty_response_delay'])
                    continue

                if response_data and 'data' in response_data and response_data['data'] is not None:
                    new_tweets = response_data['data']
                    all_tweets.extend(new_tweets)
                    num_tweets = len(new_tweets)
                    records_fetched += num_tweets
                    worker_peer_id = response_data.get('workerPeerId', 'Unknown')
                    logger.info(f"Fetched {num_tweets} tweets for {iteration_start_date.strftime('%Y-%m-%d')} to {iteration_end_date.strftime('%Y-%m-%d')} from worker {worker_peer_id}")
                    save_tweets(all_tweets, config['data_directory'], config['query'])
                    
                    # Update tweet stats
                    tweet_stats.update(num_tweets, response_time, worker_peer_id)
                    total_tweets, avg_response_time, tweets_per_minute, unique_workers = tweet_stats.get_stats()
                    logger.info(f"\033[93mTotal tweets: {total_tweets}, Avg response time: {avg_response_time:.2f}s, Tweets/min: {tweets_per_minute:.2f}, Unique workers: {unique_workers}\033[0m")
                else:
                    logger.warning(f"No tweets fetched for {iteration_start_date.strftime('%Y-%m-%d')} to {iteration_end_date.strftime('%Y-%m-%d')}. Unexpected response format: {response_data}")
                    time.sleep(config['retry_delay'])
            elif response.status_code == 429:
                logger.error(f"Received 429 error for {iteration_start_date.strftime('%Y-%m-%d')} to {iteration_end_date.strftime('%Y-%m-%d')}: {response_data}")
                logger.warning(f"Twitter API rate limit exceeded. Pausing for {config['rate_limit_delay']} seconds before retrying...")
                time.sleep(config['rate_limit_delay'])
            elif response.status_code == 417:
                logger.error(f"No workers available on the network. Response: {response_data}")
                raise NoWorkersAvailableError("No workers available on the network")
            elif response.status_code == 504:
                logger.warning(f"Received 504 error for {iteration_start_date.strftime('%Y-%m-%d')} to {iteration_end_date.strftime('%Y-%m-%d')}. Response: {response_data}")
                time.sleep(config['retry_delay'])
            elif response.status_code == 500:
                error_details = response_data.get('details', '')
                if "All workers failed" in error_details and "all accounts are rate-limited" in error_details:
                    logger.warning(f"All workers are rate-limited. Error details: {error_details}")
                    logger.warning(f"Pausing for {config['rate_limit_delay']} seconds before retrying...")
                    time.sleep(config['rate_limit_delay'])
                    continue
                else:
                    logger.error(f"Failed to fetch tweets for {iteration_start_date.strftime('%Y-%m-%d')} to {iteration_end_date.strftime('%Y-%m-%d')}: Status code {response.status_code}, Response: {response_data}")
                    break
            else:
                logger.error(f"Failed to fetch tweets for {iteration_start_date.strftime('%Y-%m-%d')} to {iteration_end_date.strftime('%Y-%m-%d')}: Status code {response.status_code}, Response: {response_data}")
                break

        except NoWorkersAvailableError as e:
            logger.warning(f"No workers available on the network: {str(e)}")
            logger.warning("Try again later when workers become available.")
            return  # Exit the function, ending the tweet fetching process
        except ReadTimeout as e:
            error_message = f"Read timeout occurred for {iteration_start_date.strftime('%Y-%m-%d')} to {iteration_end_date.strftime('%Y-%m-%d')}: {str(e)}"
            logger.warning(error_message)
            logger.debug(f"Full error details: {repr(e)}")
            
            # Try to get partial response
            if hasattr(e, 'response') and e.response is not None:
                logger.debug(f"Partial response status code: {e.response.status_code}")
                logger.debug(f"Partial response headers: {e.response.headers}")
                logger.debug(f"Partial response content: {e.response.text[:1000]}...")
            else:
                logger.debug("No partial response available")
            
            logger.warning(f"Retrying in {config['retry_delay']} seconds...")
            time.sleep(config['retry_delay'])
        except ConnectionError as e:
            logger.warning(f"Connection error occurred for {iteration_start_date.strftime('%Y-%m-%d')} to {iteration_end_date.strftime('%Y-%m-%d')}: {str(e)}")
            logger.debug(f"Full error details: {repr(e)}")
            logger.warning(f"Retrying in {config['retry_delay']} seconds...")
            time.sleep(config['retry_delay'])
        except RequestException as e:
            logger.error(f"An error occurred while fetching tweets for {iteration_start_date.strftime('%Y-%m-%d')} to {iteration_end_date.strftime('%Y-%m-%d')}: {str(e)}")
            logger.debug(f"Full error details: {repr(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.debug(f"Error response status code: {e.response.status_code}")
                logger.debug(f"Error response headers: {e.response.headers}")
                logger.debug(f"Error response content: {e.response.text[:1000]}...")
            break

    return all_tweets, api_calls_count


def fetch_tweets(config):
    api_calls_count = 0
    records_fetched = 0
    all_tweets = load_existing_tweets(config['data_directory'], config['query'])

    start_date = datetime.strptime(config['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(config['end_date'], '%Y-%m-%d').date()
    days_per_iteration = config['days_per_iteration']
    concurrent_requests = config['concurrent_requests']

    ensure_data_directory(config['data_directory'])

    logger.info("Starting to fetch tweets...")

    last_known_state = load_state()
    if last_known_state:
        current_date = datetime.strptime(last_known_state['current_date'], '%Y-%m-%d').date()
        logger.info(f"Resuming from {current_date}")
    else:
        current_date = end_date

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
        while current_date >= start_date:
            futures = []
            for _ in range(concurrent_requests):
                if current_date < start_date:
                    break
                iteration_end_date = current_date
                iteration_start_date = max(current_date - timedelta(days=days_per_iteration), start_date)
                
                future = executor.submit(
                    fetch_tweets_for_date_range, 
                    config, 
                    iteration_start_date, 
                    iteration_end_date
                )
                futures.append(future)
                
                current_date = iteration_start_date - timedelta(days=1)

            for future in concurrent.futures.as_completed(futures):
                try:
                    new_tweets, new_api_calls = future.result()
                    all_tweets.extend(new_tweets)
                    api_calls_count += new_api_calls
                    records_fetched += len(new_tweets)
                except Exception as e:
                    logger.error(f"An error occurred while fetching tweets: {str(e)}")

            save_tweets(all_tweets, config['data_directory'], config['query'])
            save_state({'current_date': current_date.strftime('%Y-%m-%d')}, api_calls_count, records_fetched, all_tweets)

    logger.info(f"Operation completed. Total API calls made: {api_calls_count}. Total records fetched: {records_fetched}")

if __name__ == "__main__":
    load_dotenv()
    config = load_config()
    logger.add(sys.stderr, format="{time} {level} {message}", filter="my_module", level=config['log_level'])
    fetch_tweets(config)

