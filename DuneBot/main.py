import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
import timezone_manager
import reddit
import database
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

    database.set_all_streams_inactive()
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

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
    else:
        # Get channel command was run in
        ctx = await bot.get_context(interaction)

        # Store channel and specified subreddit in database if subreddit exists
        if await reddit.check_subreddit_exists(subreddit) == True:
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
        
        if found == True:
            database.delete_subreddit_by_channel_id(channel_id)
            await interaction.response.send_message("Subreddit stream stopped")
        else:
            await interaction.response.send_message("No subreddit stream active in channel")


@bot.tree.command(name="book_club_join")
async def book_club_join(interaction: discord.Interaction):
    user_id = interaction.user.id
    database.add_book_club_member(user_id, "")
    await interaction.response.send_message("Joined book club.")

@bot.tree.command(name="leave_book_club")
@app_commands.describe()
async def leave_book_club(interaction: discord.Interaction):
    user_id = interaction.user.id
    if database.delete_member_by_discord_id(user_id) > 0:
        await interaction.response.send_message("You have left the book club")
    else:
        await interaction.response.send_message("You are not in the book club")

@bot.tree.command(name="add_timeslot")
@app_commands.describe(timeslot = "Enter the timeslot you wish to add to the book club. Example: 11PM UTC")
async def set_subreddit_stream_channel(interaction: discord.Interaction, timeslot: str):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
    else:
        # Get channel command was run in
        ctx = await bot.get_context(interaction)
        if timezone_manager.check_time_format(timeslot):
            database.add_timeslot(timeslot)
            await interaction.response.send_message("Timeslot added.")
        else:
            await interaction.response.send_message("Specified timeslot is invalid.")

def get_timeslot_choices():

    choices = []
    timeslots = database.get_all_timeslots()

    for timeslot in timeslots:
        choices.append(app_commands.Choice(name=timeslot["timeslot"], value=timeslot["timeslot"]))

    return (choices)

@bot.tree.command(name="remove_timeslot")
async def remove_timeslot(interaction: discord.Interaction, timeslot: str):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
    else:
        database.delete_timeslot(timeslot)
        await interaction.response.send_message("Timeslot removed.")

@remove_timeslot.autocomplete('timeslot')
async def autocomplete_callback(interaction: discord.Interaction, current: str):
    # Do stuff with the "current" parameter, e.g. querying it search results...

    # Then return a list of app_commands.Choice
    return get_timeslot_choices()
    
     

@tasks.loop(seconds = 10) # repeat after every 10 seconds
async def myLoop():
    print("Loop")
    verify_channels()
    task = asyncio.create_task(start_streams())
    shield_task = asyncio.shield(task)
    print(timezone_manager.get_current_time())

    
async def start_streams():
    documents = database.get_all_documents("DuneBot", "subreddits")

    # Begins a stream for any row that is set to false, then sets the value to true
    for document in documents:
        if document["is_active"] == False:
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
        if(channel is None):
            database.delete_subreddit(document["_id"])

bot.run(os.environ.get("TOKEN"))