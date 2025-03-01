import os
from dotenv import load_dotenv, find_dotenv

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv(find_dotenv())

ENVIRONMENT = os.environ.get("ENVIRONMENT")
MODLOG_CHANNEL_ID = int(os.environ.get("MODLOG_CHANNEL_ID"))
TOKEN = os.environ.get("TOKEN")
PREFIX = "!"

OMDB_API_KEY = os.environ.get("OMDB_API_KEY")

DB_CONNECTION_STRING = os.environ.get("DB_CONNECTION_STRING")
DB_NAME = os.environ.get("DB_NAME")
db_client = MongoClient(DB_CONNECTION_STRING, server_api=ServerApi('1'))[DB_NAME]

def get_base_path():
    return os.path.dirname(os.path.abspath(__file__)) + "/"
