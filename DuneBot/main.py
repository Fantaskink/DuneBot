import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
#import reddit
#import database
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

    print(f'{bot.user} is now running.')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

    #loop.start()

@bot.event
async def on_message(message: discord.Message):
    # Ignore messages from the bot itself to prevent potential loops
    if message.author == bot.user:
        return
    
    # List of keywords to look for
    keywords = ['Leto II', 'Miles Teg', 'Golden path', 'God Emperor', 'Ghanima',
                ' Siona ', 'Tleilaxu', 'Ghola', 'Futar', ' Rakis ', 'Stone Burner',
                'T-probe', 'Axolotl Tank', 'Honored Matres', 'The Scattering',
                'Famine Times', 'Laza Tiger', 'D-wolves', 'No-ship', 'No-room',
                'Gammu', 'Jacurutu', 'Siaynoq', 'Shuloch', 'Hayt', 'Spider Queen',
                'Daniel and Marty', 'Lampadas']
    
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

def is_marked_spoiler(text, keyword):
    pattern = rf'.*\|\|.*{re.escape(keyword)}.*\|\|.*'
    return re.match(pattern, text)

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
