import asyncpraw

import os

reddit = asyncpraw.Reddit(
    client_id = os.environ.get("CLIENT_ID"),
    client_secret = os.environ.get("CLIENT_SECRET"),
    user_agent = os.environ.get("USER_AGENT")
)


async def stream_subreddits():

    subreddit = await reddit.subreddit("dune")
    async for submission in subreddit.stream.submissions(skip_existing=False):
        print(submission)
