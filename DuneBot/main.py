import discord
from discord.ext import commands
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