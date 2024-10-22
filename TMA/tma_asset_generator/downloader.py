import logging
import os
from typing import Tuple, Optional
from PIL import Image
from io import BytesIO
import aiohttp
from datetime import datetime

class ImageDownloader:
    """Downloads images from given URLs."""

    async def download_image(self, session: aiohttp.ClientSession, image_url: str, prompt: str, validation_question: str, batch_dir: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Download an image from the provided URL.

        :param session: aiohttp client session.
        :param image_url: URL of the image to download.
        :param prompt: Prompt used to generate the image.
        :param validation_question: Validation question to embed into image metadata.
        :param batch_dir: Directory where the image will be saved.
        :return: Tuple containing the image path and image URL, or (None, None) if failed.
        """
        try:
            async with session.get(image_url) as response:
                if response.status == 200:
                    img_data = await response.read()
                    img = Image.open(BytesIO(img_data))
                    
                    # Sanitize the prompt and create a unique filename
                    sanitized_prompt = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in prompt[:20])
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    image_path = os.path.join(batch_dir, f"{sanitized_prompt.replace(' ', '_')}_{timestamp}.png")
                    
                    img.save(image_path)
                    logging.info(f"Image saved to {image_path}")
                    return image_path, image_url
                else:
                    logging.error(f"Failed to download image. Status: {response.status}")
                    return None, None
        except Exception as e:
            logging.error(f"Error downloading image: {e}")
            return None, None
