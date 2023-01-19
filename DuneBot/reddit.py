import asyncpraw
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())



async def stream_subreddit(channel, sub):
    async with asyncpraw.Reddit(
    client_id = os.environ.get("CLIENT_ID"),
    client_secret = os.environ.get("CLIENT_SECRET"),
    user_agent = os.environ.get("USER_AGENT")
) as reddit:
    
        subreddit = await reddit.subreddit(str(sub))
        print("Subreddit:", subreddit)
        async for submission in subreddit.stream.submissions(skip_existing=False):
            await send_submission(channel, submission)

async def send_submission(channel, submission):

    posttype = "New post"
    user_link = str("https://www.reddit.com/u/" + submission.author.name)
    link = "https://www.reddit.com" + submission.permalink

    if submission.is_self:
        posttype = "New self post"
        color_hex = discord.Colour.blue()
    else:
        color_hex = discord.Colour.green()
        posttype = "New link post"

    discord_embed=discord.Embed(title=str(posttype),
    url=str(link),
    description=str(submission.title),
    color=color_hex)

    discord_embed.set_author(name=str(submission.author.name), 
    url=user_link)

    await channel.send(embed=discord_embed)
    print("Sent submission in channel:", channel)