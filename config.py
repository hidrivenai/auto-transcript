# config.py
import os
from dotenv import load_dotenv

load_dotenv()

REQUIRED = ['ELEVENLABS_API_KEY', 'ONEDRIVE_REMOTE', 'GDRIVE_REMOTE']

def load_config() -> dict:
    for key in REQUIRED:
        if not os.environ.get(key):
            raise ValueError(f"Missing required environment variable: {key}")
    return {
        'elevenlabs_api_key': os.environ['ELEVENLABS_API_KEY'],
        'onedrive_remote': os.environ['ONEDRIVE_REMOTE'],
        'gdrive_remote': os.environ['GDRIVE_REMOTE'],
        'poll_interval': int(os.environ.get('POLL_INTERVAL_SECONDS', '300')),
    }
