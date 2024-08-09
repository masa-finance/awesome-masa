import json
import logging
import os
from datetime import datetime
import colorlog

def setup_logging(log_level, log_format):
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s' + log_format,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    ))

    logging.basicConfig(level=numeric_level, handlers=[handler])

def ensure_data_directory(directory):
    os.makedirs(directory, exist_ok=True)
    logging.info(f"Utilizing data directory {directory}.")

def save_all_messages(messages, data_directory, channel_id):
    filename = f'{data_directory}/{channel_id}_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.json'
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(messages, file, ensure_ascii=False, indent=2)
    logging.info(f"All Discord messages for channel {channel_id} saved to {filename} in {data_directory}.")
