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
    await make_poll()

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

@bot.tree.command(name="book_club_leave")
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
        if timezone_manager.check_timeslot_format(timeslot):
            database.add_timeslot(timeslot)
            await interaction.response.send_message("Timeslot added.")
        else:
            await interaction.response.send_message("Specified timeslot is invalid.")

# Return list of timeslot choices from database
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

@bot.tree.command(name="add_meeting")
@app_commands.describe(date = "Enter the start and end date for the week in the following format: May 31-Jun 6 ", description = "Enter the description for which section to read.")
async def add_meeting(interaction: discord.Interaction, date: str, description: str):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
    else:
        # Get channel command was run in
        ctx = await bot.get_context(interaction)
        start_date, end_date = date.split("-")
        if timezone_manager.date_to_datetime(start_date) is not False and timezone_manager.date_to_datetime(end_date) is not False:
            
            database.add_meeting(start_date, end_date, description)
            await interaction.response.send_message("Meeting added.")
        else:
            await interaction.response.send_message("Specified date is invalid.")

@tasks.loop(seconds = 10) # repeat after every 10 seconds
async def myLoop():
    verify_channels()
    task = asyncio.create_task(start_streams())
    shield_task = asyncio.shield(task)
    check_time()
    await get_poll_results()


async def start_streams():
    documents = database.get_all_documents("DuneBot", "subreddits")

    # Begins a stream for any document with "is_active" set to false, then sets the value to true
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

@bot.tree.command(name="set_poll_channel")
async def set_poll_channel(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
    else:
        # Get channel command was run in
        ctx = await bot.get_context(interaction)
        channel_id = ctx.channel.id

        database.add_channel(channel_id, "poll_channel")
        await interaction.response.send_message("Poll channel set")

async def generate_emotes(timeslots):

    emote_list = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭", "🇮", "🇯", "🇰", "🇱", "🇲", "🇳", "🇴", "🇵", "🇶", "🇷", "🇸", "🇹", "🇺", "🇻", "🇼", "🇽", "🇾", "🇿"]

    emotes = []
    
    for i in range(0,len(timeslots)):
        emotes.append(emote_list[i])
    
    return emotes

async def make_poll():
    guild = bot.guilds[0]

    target_channel_id = 0
    channels = database.get_all_channels()

    # Get id of poll channel
    for channel in channels:
        if channel["channel_function"] == "poll_channel":
            target_channel_id = int(channel["channel_id"])
    
    target_channel = bot.get_channel(target_channel_id)

    timeslots = database.get_all_timeslots()
    message = "Vote on the timeslot that suits you the best. You can only vote on one timeslot"

    poll_question = ""

    emotes = await generate_emotes(timeslots)
    print(emotes)

    for timeslot in timeslots:
        emote = emotes[timeslots.index(timeslot)]
        poll_question = poll_question + f"{emote}" + " " + str(timeslot["timeslot"]) + "\n"

    role = discord.utils.get(guild.roles, name="Book Club")
    
    poll_message = await target_channel.send(f"Make sure to vote on which time slots to use for the book club meetings {role.mention}", embed=discord.Embed(title=message, description=poll_question))
    
    for emote in emotes:
        await poll_message.add_reaction(emote)

    database.set_poll_message(poll_message.id)

async def get_poll_results():

    channels = database.get_all_channels()

    # Get id of poll channel
    target_channel_id = 0
    for channel in channels:
        if channel["channel_function"] == "poll_channel":
            target_channel_id = int(channel["channel_id"])

    target_channel = bot.get_channel(target_channel_id)

    message_document = database.get_poll_message_id()
    message_id = message_document["message_id"]
    try:
        message = await target_channel.fetch_message(message_id)
    except Exception:
        print("No poll message")
        return

    reactions = message.reactions

    for reaction in reactions:
        # I do not actually recommend doing this.
        async for user in reaction.users():
            pass
            #print(f'{user} has reacted with {reaction.emoji}!')


def begin_meeting(meeting, timeslot):
    print("begin meeting")

def check_time():
    meetings = database.get_meetings()
    timeslots = database.get_all_timeslots()

    for meeting in meetings:
        meeting_datetime = timezone_manager.date_to_datetime(meeting["start_date"])
        print("Meeting date", meeting_datetime)
        print("Current", timezone_manager.get_current_time())
        if meeting["has_been_held"] is False and timezone_manager.is_past_datetime(meeting_datetime) is True:
            for timeslot in timeslots:
                current = timezone_manager.get_current_time()
                date_time = timezone_manager.string_to_datetime(timeslot["timeslot"])
                print("Current time:", current)
                print("Timeslot", date_time)
                if timezone_manager.is_past_datetime(date_time) and timeslot["has_been_held"] == False:
                    begin_meeting(meeting, timeslot)
                    database.set_timeslot_status(timeslot["_id"])


bot.run(os.environ.get("TOKEN"))