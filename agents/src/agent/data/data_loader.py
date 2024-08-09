from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.agent.data.tweet_preprocessor import load_and_process_tweets

def load_documents(file_paths):
    docs = []
    for file_path in file_paths:
        if file_path.endswith('.json'):
            tweets = load_and_process_tweets(file_path)
            docs.extend(tweets)
        # ... existing code for other file types ...

    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=250, chunk_overlap=0
    )

    # Join the list of tweets into a single string, then split
    combined_text = "\n".join(docs)
    doc_splits = text_splitter.split_text(combined_text)
    return doc_splits