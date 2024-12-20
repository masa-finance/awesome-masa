import os
import logging
import asyncio
from datetime import datetime
import pandas as pd
import duckdb
from typing import List, Optional
from .prompts import PromptGenerator
from .images import ImageGenerator
from .client import OpenAIClient
from PIL import Image

class BatchProcessor:
    """Processes batch jobs to generate prompts and images, and save metadata."""

    def __init__(self, client: OpenAIClient, image_dir: str = 'generated_images'):
        """
        Initialize the BatchProcessor.

        :param client: Instance of OpenAIClient.
        :param image_dir: Directory to save generated images.
        """
        self.prompt_generator = PromptGenerator(client)
        self.image_generator = ImageGenerator(client, image_dir=image_dir)
        self.image_dir = image_dir
        logging.info("BatchProcessor initialized.")

    async def run_batch_job(self, num_prompts: int):
        """
        Run the batch job to generate prompts and images, and save metadata.

        :param num_prompts: Number of prompts to generate.
        """
        # Generate a unique batch ID using the current timestamp
        batch_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        batch_id = f"batch_{batch_timestamp}"
        batch_dir = os.path.join(self.image_dir, batch_id)
        os.makedirs(batch_dir, exist_ok=True)  # Create the batch directory
        logging.info(f"Batch ID: {batch_id}")
        logging.info(f"Saving images to subfolder: {batch_dir}")

        logging.info(f"Generating {num_prompts} prompts...")
        prompts = await self.prompt_generator.generate_prompts(num_prompts)
        prompts = [prompt for prompt in prompts if prompt is not None]
        logging.info(f"Generated {len(prompts)} prompts.")

        logging.info("Generating images for prompts...")
        # Record the start time for image generation
        generation_start_time = datetime.now()
        image_data = await self.image_generator.generate_images_for_prompts(prompts, batch_dir)
        generation_end_time = datetime.now()
        logging.info("Image generation complete.")

        metadata = []
        for prompt, (image_path, image_url) in zip(prompts, image_data):
            if image_path and image_url:
                prompt_length = len(prompt['image_prompt'].split())

                # Get image resolution (Assuming PIL is used in ImageGenerator)
                try:
                    with Image.open(image_path) as img:
                        width, height = img.size
                except Exception as e:
                    logging.error(f"Error getting image size for {image_path}: {e}")
                    width, height = None, None

                
                metadata.append({
                    **prompt,
                    'prompt_length': prompt_length,
                    'image_path': image_path,
                    'image_url': image_url,
                    'image_width': width,
                    'image_height': height
                })

        if metadata:
            df = pd.DataFrame(metadata)
            parquet_file = os.path.join(batch_dir, f'image_metadata_{batch_timestamp}.parquet')
            df.to_parquet(parquet_file, engine='pyarrow')
            logging.info(f"Saved metadata to {parquet_file}")

            # Save to DuckDB
            conn = duckdb.connect()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS image_metadata AS 
                SELECT * FROM read_parquet(?)
            """, [parquet_file])
            logging.info(f"Metadata saved to DuckDB from parquet file '{parquet_file}'.")
        else:
            logging.warning("No metadata to save.")

