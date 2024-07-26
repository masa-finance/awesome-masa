# Configuration settings for the scraper

# Initial URL to scrape
INITIAL_URL = "https://www.estately.com/CA/San_Francisco_County?page=1"

# Headers for the POST request
HEADERS = {
    'accept': 'application/json',
    'Content-Type': 'application/json',
}

# Endpoint of the scraper
SCRAPER_ENDPOINT = 'http://localhost:8080/api/v1/data/web'

# Depth of the scrape
DEPTH = 1