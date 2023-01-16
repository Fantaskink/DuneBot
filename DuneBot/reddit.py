import asyncpraw
import csv_helper
import asyncio

import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

reddit = asyncpraw.Reddit(
    client_id = os.environ.get("CLIENT_ID"),
    client_secret = os.environ.get("CLIENT_SECRET"),
    user_agent = os.environ.get("USER_AGENT")
)


#async def stream_subreddits(channel, subreddit):

    

