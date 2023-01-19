import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
import csv_helper
import reddit
import os
import asyncio
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

intents = discord.Intents.default()
intents.message_content = True

global bot
bot = commands.Bot(command_prefix='!', intents = intents)

@bot.event
async def on_ready():
    csv_helper.set_all_false()
    verify_channels()

    print(f'{bot.user} is now running.')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

    

    myLoop.start()

# Set up subreddit streaming in specific channel
@bot.tree.command(name="stream_subreddit")
@app_commands.describe(subreddit = "Type the name of the subreddit you wish to stream content from.")
async def set_subreddit_stream_channel(interaction: discord.Interaction, subreddit: str):

    # Get channel command was run in
    ctx = await bot.get_context(interaction)

    # Store channel and specified subreddit in csv file
    csv_helper.set_subreddit(ctx.channel.id, subreddit)

    # Send confirmation message
    await interaction.response.send_message(f"Channel now streaming submissions from r/{subreddit}")

@tasks.loop(seconds = 10) # repeat after every 10 seconds
async def myLoop():
    print("Loop")
    task = asyncio.create_task(start_streams())
    shield_task = asyncio.shield(task)

    
async def start_streams():
    rows = csv_helper.get_rows()

    for row in rows:
        if row[2] == "False":
            channel_id = row[0]
            channel = bot.get_channel(int(channel_id))
            subreddit = row[1]
            csv_helper.set_true(rows.index(row))
            print("Row",rows.index(row), rows[rows.index(row)])
            await reddit.stream_subreddit(channel, subreddit)
            csv_helper.set_false(rows.index(row))


# Delete entire row in csv file if the channel does not exist
def verify_channels():
    rows = csv_helper.get_rows()

    for row in rows:
        channel_id = row[0]
        channel = bot.get_channel(int(channel_id))
        print("Channel:", channel)
        if(channel is None):
            csv_helper.delete_row(rows.index(row))

bot.run(os.environ.get("TOKEN"))