import json
from datetime import datetime

def load_tweets(file_path):
    """Load tweets from a file."""
    with open(file_path, 'r') as file:
        tweets = json.load(file)
    return tweets


def process_tweets(tweets):
    """Extract a comprehensive set of fields from tweets, converting timestamp to Zulu time."""
    processed_tweets = []
    for tweet in tweets:
        # Convert Unix timestamp to Zulu time (UTC)
        published_utc = datetime.utcfromtimestamp(tweet.get("Timestamp", 0)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        data = {
            "user_name": tweet.get('Username', ""),
            "name": tweet.get("Name", ""),
            "text": tweet.get('Text', ""), 
            "url": tweet.get("PermanentURL", ""),
            "published": published_utc,
            "hashtags": tweet.get("Hashtags", []),
            "is_reply": tweet.get("IsReply", False),
            "is_retweet": tweet.get("IsRetweet", False)
        }
        processed_tweets.append(data)
    return processed_tweets

# Example usage
if __name__ == "__main__":
    file_path = 'path_to_your_tweets_file.json'
    tweets = load_tweets(file_path)
    processed_tweets = process_tweets(tweets)
    print(processed_tweets)