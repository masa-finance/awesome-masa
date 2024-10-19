import os
import logging
from openai import AsyncOpenAI, OpenAIError

class OpenAIClient:
    """OpenAI Client for interacting with OpenAI APIs."""

    def __init__(self, api_key: str):
        """
        Initialize the OpenAIClient.

        :param api_key: OpenAI API key.
        """
        self.api_key = api_key
        self.client = AsyncOpenAI(api_key=self.api_key)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
        logging.info("OpenAIClient initialized.")

    async def get_client(self):
        """
        Get the OpenAI client instance.

        :return: AsyncOpenAI client instance.
        """
        return self.client