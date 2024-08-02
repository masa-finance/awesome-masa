import requests
import json
import logging
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
try:
    from config import INITIAL_URL, HEADERS, SCRAPER_ENDPOINT  # Import settings from config.py
except ImportError as e:
    logging.error(f"Failed to import from config: {e}")
    INITIAL_URL, HEADERS, SCRAPER_ENDPOINT = None, None, None

# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_data(url, depth=0):
    logging.info(f"Fetching data from {url} with depth {depth}")
    data = json.dumps({"url": url, "depth": depth})
    response = requests.post(SCRAPER_ENDPOINT, headers=HEADERS, data=data)
    if response.status_code == 200:
        logging.info(f"Successfully fetched data from {url}")
    else:
        logging.error(f"Failed to fetch data from {url} with status code {response.status_code}")
    return response.json()

def increment_url(url):
    parsed_url = urlparse(url)
    query = parse_qs(parsed_url.query)
    page = int(query.get("page", [1])[0]) + 1
    query["page"] = page
    parsed_url = parsed_url._replace(query=urlencode(query, doseq=True))
    return urlunparse(parsed_url)

logging.info("Starting scraping process")
urls_to_visit = [INITIAL_URL]
scraped_data = []
urls_processed = 0
urls_saved = 0

while urls_to_visit:
    current_url = urls_to_visit.pop(0)
    logging.info(f"Processing URL: {current_url}")
    data = fetch_data(current_url)
    urls_processed += 1
    
    # Assuming 'data' contains a list of listing URLs or an indication there are no more results
    # You need to adjust this based on the actual structure of your response
    if not data.get("data"):  # If no data is returned, assume we're done
        break
    
    for page_url in data["data"]["pages"]:
        if "https://www.estately.com/listings/info/" in page_url:
            logging.info(f"Found listing URL: {page_url}")
            listing_data = fetch_data(page_url)
            scraped_data.append(listing_data)
            urls_saved += 1
    
    # Add the next page URL to urls_to_visit
    next_page_url = increment_url(current_url)
    urls_to_visit.append(next_page_url)

# Save the scraped data to a JSON file
with open('scraped_listings.json', 'w') as f:
    json.dump(scraped_data, f)
    logging.info(f"Scraped data saved to scraped_listings.json. Total URLs processed: {urls_processed}. Total URLs saved: {urls_saved}")

logging.info("Scraping complete.")