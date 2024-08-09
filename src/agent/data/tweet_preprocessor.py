import json

def load_and_process_tweets(file_path):
    with open(file_path, 'r') as file:
        tweet_data = json.load(file)
    
    processed_tweets = []
    for tweet_entry in tweet_data:
        if tweet_entry['Error'] is None and 'Tweet' in tweet_entry:
            tweet = tweet_entry['Tweet']
            # Annotate tweet text with the username to indicate the author explicitly.
            tweet_text = f"[Author: {tweet['Username']}] {tweet['Text']}"
            processed_tweets.append(tweet_text)
    
    return processed_tweets