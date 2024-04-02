import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

ENVIRONMENT = os.environ.get("ENVIRONMENT")
MODLOG_CHANNEL_ID = int(os.environ.get("MODLOG_CHANNEL_ID"))
TOKEN = os.environ.get("TOKEN")
PREFIX = "!"
PRODUCTION_BASE_PATH = '/home/ubuntu/DuneBot/DuneBot/'
DEVELOPMENT_BASE_PATH = 'DuneBot/'

def get_base_path():
    if ENVIRONMENT == "production":
        return PRODUCTION_BASE_PATH
    elif ENVIRONMENT == "development":
        return DEVELOPMENT_BASE_PATH