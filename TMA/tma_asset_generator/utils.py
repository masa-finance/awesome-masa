import json
import logging
from typing import Optional, Dict

def parse_prompt_response(content: str) -> Optional[Dict[str, str]]:
    """
    Parse the GPT response into Image Prompt and Validation Question.

    :param content: The raw response content from GPT.
    :return: Dictionary with 'image_prompt' and 'validation_question' keys, or None if parsing fails.
    """
    try:
        prompt_data = json.loads(content)
        image_prompt = prompt_data.get("image_prompt", "").strip()
        validation_question = prompt_data.get("validation_question", "").strip()
        return {
            "image_prompt": image_prompt,
            "validation_question": validation_question,
        }
    except json.JSONDecodeError as e:
        logging.error(f"JSON parsing error: {e}")
        return None