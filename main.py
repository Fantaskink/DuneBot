import discord
from discord.ext import commands
from config import TOKEN, db_client

try:
    db_client.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)


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

bot.run(TOKEN)

"""
async def update_presence():
    days_until_string = await get_days_until_string("2024-03-01", "00:00")

    #days_until_string = "ITS FUCKING DELAYED"

    activity = discord.CustomActivity(name=days_until_string)
    await bot.change_presence(activity=activity)
    

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