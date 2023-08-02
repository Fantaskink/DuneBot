import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
#import reddit
#import database
from datetime import date
import csv
import os
import asyncio
import re
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

intents = discord.Intents.default()
intents.message_content = True

global bot
bot = commands.Bot(command_prefix='!', intents=intents)

environment = os.environ.get("ENVIRONMENT")
print("Environment:", environment)


@bot.event
async def on_ready():

    #database.set_all_streams_inactive()
    #verify_channels()

    update_presence_task.start()

    print(f'{bot.user} is now running.')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

    #loop.start()

@bot.event
async def on_message(message: discord.Message):
    await check_spoiler(message)
    

async def check_spoiler(message):
    # Ignore messages from the bot itself to prevent potential loops
    if message.author == bot.user:
        return
    
    # List of keywords to look for
    keywords = await get_spoiler_keywords()
    
    if environment == "production":
        modlog_channel = bot.get_channel(701710310121275474)
        channel_ids = [
                   701674250591010840,  #general
                   768612534076833864,  #filmbook
                   751681926527582329,  #cinematv
                   751682462001659986,  #nondunebooks
                   751684353523843165,  #games
                   753460736579207208,  #offtopic
                   715906624887193702,  #baliset
                   701883990369370134,  #sietchposting
                   702080128997654548,  #first time reader
                   701690551996776459,  #moviesofdune
                   701726640719396905,  #gamesofdune
                   1068027156455755806, #heretical
                   ]
    elif environment == "development":
        modlog_channel = bot.get_channel(1131571647665672262)
        channel_ids = [1130972092570009632] #test channel
    

    # Check if the message is from the desired channel (replace 'CHANNEL_ID' with your channel ID)
    for id in channel_ids:
        if message.channel.id == id:
            # Process the message for keywords
            for keyword in keywords:
                if keyword.lower() in message.content.lower() and not is_marked_spoiler(message.content.lower(), keyword.lower()):
                    await message.reply(f"Please be mindful of spoilers in this channel! Surround spoilers with '||' when discussing plot points from later books.")
                    await modlog_channel.send(f"Spoiler reminder sent in {message.channel.mention}, triggered by keyword: {keyword}.\nJump to message: {message.jump_url}")
                    break
    

    # Allow other event listeners (commands, etc.) to continue functioning
    await bot.process_commands(message)

async def get_spoiler_keywords():
    if environment == "production":
        file_path = '/home/ubuntu/DuneBot/DuneBot/csv/keywords.csv'
    elif environment == "development":
        file_path = 'DuneBot/csv/keywords.csv'
    keywords = []

    with open(file_path, 'r', newline='') as csvfile:
        csv_reader = csv.reader(csvfile, skipinitialspace=False)

        for row in csv_reader:
            if row:
                keywords.append(row[0])
    return keywords


def is_marked_spoiler(text, keyword):
    pattern = rf'.*\|\|.*{re.escape(keyword)}.*\|\|.*'
    return re.match(pattern, text)

async def update_presence():
    days_until_string = await get_days_until_string("2023-11-03")
    #game = discord.Game("with the API")
    #await bot.change_presence(status=discord.Status.idle, activity=game)

    activity = discord.Activity(type=discord.ActivityType.watching, name=days_until_string)
    await bot.change_presence(activity=activity)
    

@tasks.loop(hours=24)
async def update_presence_task():
    await update_presence()

async def get_days_until_string(target_date_str):
    # Get the current date
    today = date.today()

    target_date = date.fromisoformat(target_date_str)

    # Calculate the difference between the target date and the current date
    delta = target_date - today

    days_until = delta.days

    if days_until == 1:
        return(f"{days_until} day until Dune Part Two")
        

    if days_until <= 0:
        return(f"Dune Part Two OUT NOW!")
        
    
    return(f"{days_until} days until Dune Part Two")

@bot.tree.command(name="print_spoiler_keywords")
@app_commands.describe()
async def print_spoiler_keywords(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
        return

    keywords = await get_spoiler_keywords()
    keyword_string = ""
    for keyword in keywords:
        keyword_string = keyword_string + (str(keywords.index(keyword)) + ":" + keyword + "\n")

    await interaction.response.send_message("```" + keyword_string + "```")


@bot.tree.command(name="add_spoiler_keyword")
@app_commands.describe(keyword="Type in a keyword you wish to be considered a spoiler.")
async def add_spoiler_keyword(interaction: discord.Interaction, keyword: str):

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
        return
    
    if environment == "production":
        file_path = '/home/ubuntu/DuneBot/DuneBot/csv/keywords.csv'
    elif environment == "development":
        file_path = 'DuneBot/csv/keywords.csv'

    with open(file_path, 'a') as csv_file:
            csv_file.write(keyword + ",\n")
    
    await interaction.response.send_message(f"Keyword: {keyword} added.")

@bot.tree.command(name="delete_spoiler_keyword")
@app_commands.describe(index="Type in the index of the spoiler keyword you wish to remove.")
async def delete_spoiler_keyword(interaction: discord.Interaction, index: int):

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
        return
    
    if environment == "production":
        file_path = '/home/ubuntu/DuneBot/DuneBot/csv/keywords.csv'
    elif environment == "development":
        file_path = 'DuneBot/csv/keywords.csv'
        
    with open(file_path, 'r', newline='') as csv_file:
        reader = csv.reader(csv_file)
        data = list(reader)

        # Check if the row_index is valid
    if index < 0 or index >= len(data):
        await interaction.response.send_message("Invalid index", ephemeral=True)
        return
    
    # Remove the desired row
    data.pop(index)

    # Write the modified data back to the CSV file
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)
    
    await interaction.response.send_message(f"Keyword removed.")
'''



# Set up subreddit streaming in specific channel
@bot.tree.command(name="stream_subreddit")
@app_commands.describe(subreddit="Type the name of the subreddit you wish to stream content from.")
async def set_subreddit_stream_channel(interaction: discord.Interaction, subreddit: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
    else:
        # Get channel command was run in
        ctx = await bot.get_context(interaction)

        # Store channel and specified subreddit in database if subreddit exists
        if await reddit.check_subreddit_exists(subreddit):
            database.add_subreddit(ctx.channel.id, subreddit)
            # Send confirmation message
            await interaction.response.send_message(f"Channel now streaming submissions from r/{subreddit}")
        else:
            await interaction.response.send_message(f"r/{subreddit} does not exist")


@bot.tree.command(name="stop_stream")
@app_commands.describe()
async def stop_subreddit_stream_channel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
    else:
        # Get channel command was run in
        ctx = await bot.get_context(interaction)
        channel_id = ctx.channel.id

        subreddits = database.get_all_documents("DuneBot", "subreddits")

        found = False

        for subreddit in subreddits:
            if channel_id == subreddit["channel_id"]:
                found = True

        if found:
            database.delete_subreddit_by_channel_id(channel_id)
            await interaction.response.send_message("Subreddit stream stopped")
        else:
            await interaction.response.send_message("No subreddit stream active in channel")




@tasks.loop(seconds=10)  # repeat after every 10 seconds
async def loop():
    #print("Loop")
    verify_channels()
    task = asyncio.create_task(start_streams())
    shield_task = asyncio.shield(task)


async def start_streams():
    documents = database.get_all_documents("DuneBot", "subreddits")

    # Begins a stream for any document with "is_active" set to false, then sets the value to true
    for document in documents:
        if not document["is_active"]:
            channel_id = document["channel_id"]
            channel = bot.get_channel(int(channel_id))
            subreddit = document["subreddit"]
            database.set_activity_status(document["_id"], True)
            print("Beginning stream for:", subreddit, "in", bot.get_channel(int(channel_id)))
            await reddit.stream_subreddit(channel_id, channel, subreddit)
            print("stream function terminated")
            database.set_activity_status(document["_id"], False)


# Delete database document if its channel_id does not match a channel on the server
def verify_channels():
    documents = database.get_all_documents("DuneBot", "subreddits")

    for document in documents:
        channel_id = document["channel_id"]
        channel = bot.get_channel(int(channel_id))
        if channel is None:
            database.delete_subreddit(document["_id"])

            
'''


bot.run(os.environ.get("TOKEN"))
