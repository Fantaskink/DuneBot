import discord
from discord.ext import commands
from discord.ext import tasks
from datetime import date, datetime, time, timedelta
from config import TOKEN

intents = discord.Intents.all()
intents.message_content = True

cogs: list = ["Functions.wordle", "Functions.admin", "Functions.spoiler", 
              "Functions.media", "Functions.hall_of_fame", "Functions.misc", 
              "Functions.encyclopedia", "Functions.nitro"]

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    for cog in cogs:
        try:
            print(f"Loading {cog}")
            await bot.load_extension(cog)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(cog, exc))

    #update_presence_task.start()

    #print(f'{bot.user} is now running.')

"""
async def update_presence():
    days_until_string = await get_days_until_string("2024-03-01", "00:00")

    #days_until_string = "ITS FUCKING DELAYED"

    activity = discord.CustomActivity(name=days_until_string)
    await bot.change_presence(activity=activity)
    

@tasks.loop(hours=24)
async def update_presence_task():
    await update_presence()
    

async def get_days_until_string(target_date_str, time_str):
    # Get the current date
    today = datetime.now()

    # Parse the target date and time from the input strings
    target_date = date.fromisoformat(target_date_str)
    target_time = time.fromisoformat(time_str)

    # Combine the target date and time into a single datetime object
    target_datetime = datetime.combine(target_date, target_time)

    # Calculate the time difference between the target datetime and the current datetime
    delta = target_datetime - today

    days_until = delta.days

    if days_until == 1:
        return(f"{days_until} day until Dune Part Two")
        
    if days_until <= 0:
        return(f"Dune Part Two OUT NOW!")
    
    return(f"{days_until} days until Dune Part Two")



"""

bot.run(TOKEN)

"""
@bot.tree.command(name="meme")
@app_commands.describe(top_text="Top text", bottom_text="Bottom text", image_link="Image link")
async def meme(interaction: discord.Interaction, top_text: str, bottom_text: str, image_link: str):
    from PIL import Image, ImageDraw, ImageFont
    import requests
    from io import BytesIO

    await interaction.response.defer(ephemeral=True)
    
    # Load the image from the link
    response = requests.get(image_link)
    img = Image.open(BytesIO(response.content))

    file_path = base_path + 'impact.tff'

    # Load Impact font
    font = ImageFont.truetype(file_path, 40)  # Make sure you have the "impact.ttf" file in the same directory

    # Initialize the drawing context
    draw = ImageDraw.Draw(img)

    # Calculate text bounding boxes
    top_text_bbox = draw.textbbox((0, 0), top_text, font=font)
    bottom_text_bbox = draw.textbbox((0, 0), bottom_text, font=font)

    # Calculate text positions
    width, height = img.size
    top_text_position = ((width - top_text_bbox[2]) / 2, 10)
    bottom_text_position = ((width - bottom_text_bbox[2]) / 2, height - bottom_text_bbox[3] - 10)

    # Draw top and bottom text on the image
    draw.text(top_text_position, top_text, fill="white", font=font)
    draw.text(bottom_text_position, bottom_text, fill="white", font=font)

    # Save the modified image to a BytesIO object
    modified_img_io = BytesIO()
    img.save(modified_img_io, format="PNG")
    modified_img_io.seek(0)

    # Create a Discord File object
    modified_img_file = discord.File(modified_img_io, filename="meme.png")

    await interaction.followup.send(file=modified_img_file)

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


@bot.tree.command(name="encyclopedia")
@app_commands.describe(keyword="Type in the name of the entry you wish to look up.")
async def encyclopedia(interaction: discord.Interaction, keyword: str):
    file_path = base_path + 'csv/encyclopedia.csv'

    with open(file_path, 'r', newline='') as csvfile:
        csv_reader = csv.reader(csvfile, skipinitialspace=False)

        for row in csv_reader:
            if row:
                if row[0].lower() == keyword.lower():
                    page_count = len(row) - 1
                    view = Pages(page_count)
                    await interaction.response.send_message(row[1], view=view)
                    await view.wait()
                    if view.index is None:
                        await interaction.response.edit_message(view=view)
                    elif view.index:
                        print("index" + str(view.index))
                        await interaction.response.edit_message(view=view)
                    else:
                        print('Cancelled...')

    await interaction.response.send_message(f"Entry not found.", ephemeral=True)
"""