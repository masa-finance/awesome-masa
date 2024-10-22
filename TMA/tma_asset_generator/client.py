import os
import logging
from openai import AsyncOpenAI, OpenAIError
from dotenv import load_dotenv

class OpenAIClient:
    """OpenAI Client for interacting with OpenAI APIs."""

    def __init__(self):
        load_dotenv(dotenv_path='.env')  # Load environment variables from .env
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logging.error("OPENAI_API_KEY not found in environment variables.")
            raise EnvironmentError("OPENAI_API_KEY not set.")
        self.client = AsyncOpenAI(api_key=self.api_key)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
        logging.info("OpenAIClient initialized with API key.")

    async def get_client(self):
        """
        Get the OpenAI client instance.

        :return: Instance of AsyncOpenAI client.
        :raises OpenAIError: If an error occurs while getting the client.
        """
        try:
            return self.client
        except OpenAIError as e:
            logging.error(f"Error getting OpenAI client: {e}")
            raise
