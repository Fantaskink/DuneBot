import asyncpraw
import os
import discord
from discord.ext import commands
from database import get_all_documents
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


async def stream_subreddit(channel_id, channel, sub):
    async with asyncpraw.Reddit(
            client_id=os.environ.get("CLIENT_ID"),
            client_secret=os.environ.get("CLIENT_SECRET"),
            user_agent=os.environ.get("USER_AGENT")
    ) as reddit:

        # Retrieve subreddit instance using subreddit name
        subreddit = await reddit.subreddit(str(sub))
        async for submission in subreddit.stream.submissions(skip_existing=True):
            documents = get_all_documents("DuneBot", "subreddits")

            channel_and_sub_valid = False

            for document in documents:

                if channel_id == document["channel_id"] and sub == document["subreddit"] and document[
                    "is_active"] == True:
                    channel_and_sub_valid = True

            if channel_and_sub_valid == True:
                await send_submission(channel, submission)
            else:
                print("Channel and sub no longer valid")
                break
    print("Function halted")


async def send_submission(channel, submission):
    # Get post selftext
    try:
        data = submission.selftext
    except:
        print("Failed to load post")

    # Get post author
    user = submission.author
    await user.load()

    # Attempt to load user icon. Load default icon if unsuccessful
    try:
        icon = user.icon_img
    except:
        icon = "https://www.redditstatic.com/avatars/avatar_default_12_545452.png"

    # Shorten and add dots
    post_text = (data[:200] + '...') if len(data) > 75 else data

    # Add spoiler tags to selftext if spoiler
    if submission.spoiler and not post_text == "":
        post_text = "||" + post_text + "||"

    # Get links to author and post
    user_link = str("https://www.reddit.com/u/" + submission.author.name)
    link = "https://www.reddit.com" + submission.permalink

    posttype = "New post"

    is_media = False

    if submission.is_self:
        posttype = "New self post"
        color_hex = discord.Colour.blue()
    else:
        posttype = "New link post"
        color_hex = discord.Colour.green()
        is_media = True

    discord_embed = discord.Embed(title=str(posttype),
                                  url=str(link),
                                  color=color_hex)

    discord_embed.set_author(name=str(submission.author.name),
                             url=user_link,
                             icon_url=str(icon)
                             )

    post_name = submission.title

    # Shorten post title and add dots
    post_name_shortened = (post_name[:200] + '...') if len(post_name) > 75 else post_name

    if is_media:
        discord_embed.set_image(url=submission.url)
        discord_embed.add_field(name=post_name_shortened, value=post_text + "\n" + submission.url, inline=False)
    else:
        discord_embed.add_field(name=post_name_shortened, value=post_text, inline=False)

    # bot.user.edit(username=submission.subreddit.name)

    await channel.send(embed=discord_embed)

    # bot.user.edit(username="Dune")
    # print("Sent submission in channel:", channel)


async def check_subreddit_exists(subreddit_name):
    async with asyncpraw.Reddit(
            client_id=os.environ.get("CLIENT_ID"),
            client_secret=os.environ.get("CLIENT_SECRET"),
            user_agent=os.environ.get("USER_AGENT")
    ) as reddit:

        try:
            subreddit = await reddit.subreddit(subreddit_name, fetch=True)
        except Exception:
            return False
        else:
            return True