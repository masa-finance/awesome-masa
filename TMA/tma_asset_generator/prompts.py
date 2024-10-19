import asyncio
import json
import logging
from typing import Dict, Optional, List
from openai import OpenAIError
from .client import OpenAIClient
from .utils import parse_prompt_response

class PromptGenerator:
    """Generates prompts using OpenAI's GPT API."""

    def __init__(self, client: OpenAIClient):
        """
        Initialize the PromptGenerator.

        :param client: Instance of OpenAIClient.
        """
        self.client = client
        logging.info("PromptGenerator initialized.")

    async def generate_prompt(self) -> Optional[Dict[str, str]]:
        """
        Generate a structured prompt containing an Image Prompt and a Validation Question.

        :return: Dictionary with 'image_prompt' and 'validation_question' keys, or None if an error occurs.
        """
        try:
            response = await self.client.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a creative AI assisting in generating prompts for an AI image generation model. "
                            "Each prompt consists of two parts: an Image Prompt and a Validation Question. "
                            "The Image Prompt should describe an image where a specific item is present but not immediately obvious, "
                            "making it a fun find for users. "
                            "Please provide the output in JSON format with 'image_prompt' and 'validation_question' keys."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Generate a creative Image Prompt and a corresponding Validation Question. "
                            "The Image Prompt should describe an image in a single sentence with a hidden item. "
                            "The Validation Question should ask if the specific hidden item is present in the image. "
                            "Please respond in the following JSON format:\n"
                            "{\n"
                            '  "image_prompt": "Your image prompt here.",\n'
                            '  "validation_question": "Your validation question here."\n'
                            "}"
                        ),
                    },
                ],
                max_tokens=150,
            )
            content = response.choices[0].message.content.strip()
            prompt_data = parse_prompt_response(content)
            if prompt_data:
                logging.info(f"Image Prompt: {prompt_data['image_prompt']}")
                logging.info(f"Validation Question: {prompt_data['validation_question']}")
                return prompt_data
            else:
                logging.error("Failed to parse the prompt response.")
                return None
        except OpenAIError as e:
            logging.error(f"Error generating prompt: {e}")
            return None

    async def generate_prompts(self, num_prompts: int) -> List[Optional[Dict[str, str]]]:
        """
        Generate multiple prompts asynchronously.

        :param num_prompts: Number of prompts to generate.
        :return: List of generated prompts.
        """
        tasks = [asyncio.create_task(self.generate_prompt()) for _ in range(num_prompts)]
        return await asyncio.gather(*tasks)