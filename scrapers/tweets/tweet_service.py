import json
import logging
import os
import time
from datetime import datetime
import re

def setup_logging(log_level, log_format):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    logging.basicConfig(level=numeric_level, format=log_format)

def ensure_data_directory(directory):
    os.makedirs(directory, exist_ok=True)

def load_existing_tweets(data_directory, query):
    sanitized_query = re.sub(r'[^\w\-_\. ]', '_', query)
    sanitized_query = sanitized_query.replace(' ', '_')
    filename = f'{data_directory}/{sanitized_query}.json'
    
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    return []

def save_tweets(tweets, data_directory, query):
    sanitized_query = re.sub(r'[^\w\-_\. ]', '_', query)
    sanitized_query = sanitized_query.replace(' ', '_')
    
    filename = f'{data_directory}/{sanitized_query}.json'
    
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(tweets, file, ensure_ascii=False, indent=2)
    logging.info(f"All tweets saved to {filename}")

def create_tweet_query(hashtag, start_date, end_date):
    return f"({hashtag} until:{end_date.strftime('%Y-%m-%d')} since:{start_date.strftime('%Y-%m-%d')})"