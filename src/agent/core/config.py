# Existing imports and configurations
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# URLs for data loading
# TODO: Extend to other data types, Web, Discord, Telegram, YouTube, and Podcast
DATA_URLS = [
    "data/twitter_data/traderxo.json",
]