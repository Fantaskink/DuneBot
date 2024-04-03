import discord
from discord import app_commands
from discord.ext import commands
import csv
import re
from typing import List
from config import get_base_path, MODLOG_CHANNEL_ID, ENVIRONMENT

SPOILER_KEYWORD_PATH = get_base_path() + 'csv/keywords.csv'

async def keyword_autocomplete( 
        interaction: discord.Interaction, 
        current: str
    ) -> List[app_commands.Choice[int]]:
        keywords = get_spoiler_keywords()
        choices = []
        for keyword in keywords:
            if len(choices) == 25:
                break
            if current.lower() in keyword.lower():
                choices.append(app_commands.Choice(name=keyword, value=str(keywords.index(keyword))))
        return choices

class SpoilerCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        await self.check_spoiler(message)

    @app_commands.command(name="add_spoiler_keyword")
    @app_commands.describe(keyword="Type in a keyword you wish to be considered a spoiler.")
    async def add_spoiler_keyword(self, interaction: discord.Interaction, keyword: str):

        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
            return

        with open(SPOILER_KEYWORD_PATH, 'a') as csv_file:
                csv_file.write(keyword + ",\n")
        
        await interaction.response.send_message(f"Keyword: {keyword} added.")
    
    @app_commands.command(name="remove_spoiler_keyword")
    @app_commands.autocomplete(index=keyword_autocomplete)
    @app_commands.guild_only()
    async def remove_spoiler_keyword(self, interaction: discord.Interaction, index: str):
        with open(SPOILER_KEYWORD_PATH, 'r') as csv_file:
            reader = csv.reader(csv_file)
            data = list(reader)

            data.pop(int(index))

            with open(SPOILER_KEYWORD_PATH, 'w', newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerows(data)
        
        await interaction.response.send_message(f"Keyword removed.")
    
    
    async def check_spoiler(self, message: discord.Message) -> None:
        # Ignore messages from the bot itself to prevent potential loops
        if message.author.bot:
            return
        
        # List of keywords to look for
        keywords = get_spoiler_keywords()

        modlog_channel = self.bot.get_channel(MODLOG_CHANNEL_ID)
        
        channel_ids = {
            "production": [
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
            ],
            "development": [1130972092570009632] #test channel
        }

        current_channel_ids = channel_ids.get(ENVIRONMENT, [])
        
        # Check if the message is from the desired channel
        for id in current_channel_ids:
            if message.channel.id == id:
                # Process the message for keywords
                for keyword in keywords:
                    if keyword.lower() in message.content.lower() and not is_marked_spoiler(message.content.lower(), keyword.lower()):
                        await message.reply(f"Please be mindful of spoilers in this channel! Surround spoilers with '||' when discussing plot points from later books.")
                        await modlog_channel.send(f"Spoiler reminder sent in {message.channel.mention}, triggered by keyword: {keyword}.\nJump to message: {message.jump_url}")
                        break

        # Allow other event listeners (commands, etc.) to continue functioning
        await self.bot.process_commands(message)


def is_marked_spoiler(text, keyword) -> bool:
    pattern = rf'.*\|\|.*{re.escape(keyword)}.*\|\|.*'
    return re.search(pattern, text, re.DOTALL)


def get_spoiler_keywords() -> List[str]:
    keywords = []
    with open(SPOILER_KEYWORD_PATH, 'r', newline='') as csvfile:
        csv_reader = csv.reader(csvfile, skipinitialspace=False)

        for row in csv_reader:
            if row:
                keywords.append(row[0])
    return keywords


def get_keyword_choices():
        choices = []
        for keyword in get_spoiler_keywords():
            choices.append(app_commands.Choice(name=keyword, value=keyword))

            return (choices)

async def setup(bot: commands.Bot) -> None: 
    await bot.add_cog(SpoilerCog(bot))