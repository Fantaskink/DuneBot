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
        async for submission in subreddit.stream.submissions(skip_existing=True):
            await send_submission(channel, submission)

async def send_submission(channel, submission):

    # Get post selftext
    try:
        data = submission.selftext
    except:
        print("Failed to load post")


    user = submission.author

    await user.load()

    try:
        icon = user.icon_img
    except:
        icon = "https://www.redditstatic.com/avatars/avatar_default_12_545452.png"

    # Shorten and add dots
    post_text = (data[:200] + '...') if len(data) > 75 else data

    # Add spoiler tags to selftext if spoiler
    if submission.spoiler:
        post_text = "||"+ post_text + "||"


    user_link = str("https://www.reddit.com/u/" + submission.author.name)
    link = "https://www.reddit.com" + submission.permalink

    posttype = "New post"

    if submission.is_self:
        posttype = "New self post"
        color_hex = discord.Colour.blue()
    else:
        posttype = "New link post"
        color_hex = discord.Colour.green()

    discord_embed=discord.Embed(title=str(posttype),
    url=str(link),
    color=color_hex)

    discord_embed.set_author(name=str(submission.author.name), 
    url=user_link,
    icon_url=str(icon)
    )

    post_name = submission.title

    # Shorten and add dots
    post_name_shortened = (post_name[:200] + '...') if len(post_name) > 75 else post_name

    discord_embed.add_field(name=post_name_shortened, value=post_text, inline=False)


    #bot.user.edit(username=submission.subreddit.name)

    await channel.send(embed=discord_embed)

    
    #bot.user.edit(username="Dune")
    #print("Sent submission in channel:", channel)