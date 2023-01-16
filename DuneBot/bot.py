import discord
from discord import app_commands
from discord.ext import commands
import reddit
import csv_helper
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

TOKEN = os.environ.get("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

def run_discord_bot():

    bot = commands.Bot(command_prefix='!', intents = intents)

    @bot.event
    async def on_ready():
        print(f'{bot.user} is now running.')
        try:
            synced = await bot.tree.sync()
            print(f"Synced {len(synced)} commands")
        except Exception as e:
            print(e)

    # Set up subreddit streaming in specific channel
    @bot.tree.command(name="set_subreddit")
    @app_commands.describe(subreddit = "Type the name of the subreddit you wish to stream content from.")
    async def set_subreddit(interaction: discord.Interaction, subreddit: str):

        # Get channel command was run in
        ctx = await bot.get_context(interaction)

        # Store channel and specified subreddit in csv file
        csv_helper.set_subreddit(ctx.channel, subreddit)

        # Send confirmation message
        await interaction.response.send_message(f"Channel now streaming submissions from r/{subreddit}")


    # Remember to run your bot with your personal TOKEN
    bot.run(TOKEN)
    