import requests
import os
import yaml
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import time
import logging
import json
from discord_service import save_all_messages, setup_logging, ensure_data_directory

def load_config():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(dir_path, 'discord_fetcher.yaml')
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def save_state(state, api_calls_count, records_fetched, all_messages):
    state_data = {
        'last_known_state': state,
        'api_calls_count': api_calls_count,
        'records_fetched': records_fetched,
        'all_messages_sample': all_messages[:10]  # Save a sample of the first 10 messages for visibility
    }
    with open('scrapers/discord/last_known_discord_state_detailed.json', 'w') as f:
        json.dump(state_data, f, indent=4)

def load_state():
    file_path = 'scrapers/discord/last_known_discord_state_detailed.json'
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f).get('last_known_state', {})
        except json.JSONDecodeError:
            return {}
    else:
        with open(file_path, 'w') as f:
            json.dump({'last_known_state': {}}, f)
        return {}

def fetch_messages(config):
    start_time = datetime.now()  # Define start_time when fetch_messages is called
    api_calls_count = 0
    records_fetched = 0
    all_messages = []
    

    logging.info("Starting to fetch Discord messages...")

    api_url = config['api_endpoint'].format(channel_id=config['channel_id'])
    params = {
        "limit": config['messages_per_request']
    }

    last_message_id = None
    iterations = config.get('iterations', None)
    iteration_count = 0
    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)

    # Load the last known state
    last_known_state = load_state()
    if last_known_state:
        last_message_id = last_known_state.get('last_message_id')
        latest_date = datetime.fromisoformat(last_known_state['current_date'])
        logging.info(f"Resuming from message ID {last_message_id} and date {latest_date}")
        print()
    else:
        latest_date = None

    while True:
        if last_message_id:
            params['before'] = last_message_id


        response = requests.get(api_url, headers=config['headers'], params=params, timeout=60)
        api_calls_count += 1

        # Log rate limit information
        if 'X-RateLimit-Limit' in response.headers:
            logging.info(f"X-RateLimit-Limit: {response.headers['X-RateLimit-Limit']} - The number of requests that can be made")
        if 'X-RateLimit-Remaining' in response.headers:
            logging.info(f"X-RateLimit-Remaining: {response.headers['X-RateLimit-Remaining']} - The number of remaining requests that can be made")
        if 'X-RateLimit-Reset' in response.headers:
            logging.info(f"X-RateLimit-Reset: {response.headers['X-RateLimit-Reset']} - Epoch time at which the rate limit resets")
        if 'X-RateLimit-Reset-After' in response.headers:
            logging.info(f"X-RateLimit-Reset-After: {response.headers['X-RateLimit-Reset-After']} - Total time (in seconds) of when the current rate limit bucket will reset")
        if 'X-RateLimit-Bucket' in response.headers:
            logging.info(f"X-RateLimit-Bucket: {response.headers['X-RateLimit-Bucket']} - A unique string denoting the rate limit being encountered")

        if response.status_code == 403:
            logging.error(f"Error fetching channel messages: Forbidden (403). Please check your authentication and permissions.")
            break
        elif response.status_code != 200:
            logging.error(f"Failed to fetch messages. Status code: {response.status_code}. Response: {response.text}")
            break
        else:
            response_data = response.json()
            if not response_data or 'data' not in response_data or not response_data['data']:
                logging.warning("No messages fetched.")
                break
            else:
                messages = response_data['data']
                all_messages.extend(messages)
                num_messages = len(messages)
                records_fetched += num_messages
                logging.info(f"Successfully fetched {num_messages} messages.")

                # Extract the latest date and id from the last message
                if messages:
                    last_message_id = messages[-1].get('id')
                    latest_timestamp = messages[-1].get('timestamp')
                    if latest_timestamp:
                        latest_date = datetime.fromisoformat(latest_timestamp.rstrip('Z'))
                        formatted_date = latest_date.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Truncate microseconds to milliseconds
                        # Save the detailed state after a successful fetch
                        save_state({'current_date': formatted_date, 'last_message_id': last_message_id}, api_calls_count, records_fetched, all_messages)
                        logging.info(f"Latest date and time {formatted_date} and message ID {last_message_id} saved to last_known_discord_state_detailed.json")
                        print()  # Adding a print statement for some spacing
                    else:
                        logging.warning("No timestamp found in the last message.")
                else:
                    logging.warning("No messages to extract date from.")
                    print()  # Adding a print statement for some spacing

        time.sleep(config['request_delay'])

        iteration_count += 1
        logging.info(f"Completed iteration {iteration_count} of {iterations}")
        if iterations and iteration_count >= iterations:
            break
        if latest_date and latest_date < one_year_ago:
            break

    end_time = datetime.now()
    total_time = end_time - start_time
    save_all_messages(all_messages, config['data_directory'], config['channel_id'])
    logging.info(f"Operation completed. Total API calls made: {api_calls_count}. Total records fetched: {records_fetched}. Total time taken: {total_time}")

if __name__ == "__main__":
    load_dotenv()
    config = load_config()
    setup_logging(config['log_level'], config['log_format'])
    ensure_data_directory(config['data_directory'])
    fetch_messages(config)