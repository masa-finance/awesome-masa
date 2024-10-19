import logging
from typing import Tuple, Optional, List
from openai import OpenAIError
import aiohttp
import asyncio
from PIL import Image
from io import BytesIO
import os
from .client import OpenAIClient
from .downloader import ImageDownloader

class ImageGenerator:
    """Generates images based on prompts using OpenAI's API."""

    def __init__(self, client: OpenAIClient, image_dir: str = 'generated_images'):
        """
        Initialize the ImageGenerator.

        :param client: Instance of OpenAIClient.
        :param image_dir: Directory to save generated images.
        """
        self.client = client
        self.image_dir = image_dir
        os.makedirs(self.image_dir, exist_ok=True)
        logging.info(f"ImageGenerator initialized with directory: {self.image_dir}")

    async def generate_image_from_prompt(self, session: aiohttp.ClientSession, prompt: str, validation_question: str, batch_dir: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate an image based on the prompt using OpenAI's API.

        :param session: aiohttp client session.
        :param prompt: Prompt used to generate the image.
        :param validation_question: Validation question associated with the prompt.
        :param batch_dir: Directory where the image will be saved.
        :return: Tuple containing the image path and image URL, or (None, None) if an error occurs.
        """
        try:
            response = await self.client.client.images.generate(
                prompt=prompt,
                model="dall-e-3",
                n=1,
                size="1024x1024"
            )
            image_url = response.data[0].url
            downloader = ImageDownloader()
            # Pass validation_question to the downloader
            return await downloader.download_image(session, image_url, prompt, validation_question, batch_dir)
        except OpenAIError as e:
            logging.error(f"Error generating image for prompt: {prompt}. Error: {e}")
            return None, None

    async def generate_images_for_prompts(self, prompts: list, batch_dir: str) -> List[Tuple[Optional[str], Optional[str]]]:
        """
        Generate images for all prompts concurrently.

        :param prompts: List of prompt dictionaries containing 'image_prompt' and 'validation_question'.
        :param batch_dir: Directory where images will be saved.
        :return: List of tuples containing image paths and image URLs.
        """
        async with aiohttp.ClientSession() as session:
            tasks = [
                asyncio.create_task(
                        self.generate_image_from_prompt(
                            session,
                            prompt["image_prompt"],
                            prompt["validation_question"],
                            batch_dir
                        )
                    ) for prompt in prompts if prompt
                ]
            return await asyncio.gather(*tasks)
