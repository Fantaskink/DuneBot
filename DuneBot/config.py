import os
from dotenv import load_dotenv, find_dotenv

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv(find_dotenv())

ENVIRONMENT = os.environ.get("ENVIRONMENT")
MODLOG_CHANNEL_ID = int(os.environ.get("MODLOG_CHANNEL_ID"))
TOKEN = os.environ.get("TOKEN")
PREFIX = "!"
PRODUCTION_BASE_PATH = '/home/andreas/DiscordBots/DuneBot/DuneBot/'
DEVELOPMENT_BASE_PATH = 'DuneBot/'

OMDB_API_KEY = os.environ.get("OMDB_API_KEY")

DB_CONNECTION_STRING = os.environ.get("DB_CONNECTION_STRING")

DB_NAME = os.environ.get("DB_NAME")

db_client = MongoClient(DB_CONNECTION_STRING, server_api=ServerApi('1'))

def get_base_path():
    if ENVIRONMENT == "production":
        return PRODUCTION_BASE_PATH
    elif ENVIRONMENT == "development":
        return DEVELOPMENT_BASE_PATH