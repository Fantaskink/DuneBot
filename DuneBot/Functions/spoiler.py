import discord
from discord import app_commands
from discord.ext import commands
import re
from typing import List
from config import MODLOG_CHANNEL_ID, db_client, DB_NAME


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

        db_client[DB_NAME]["Spoiler Keywords"].insert_one({"keyword": keyword})
        
        await interaction.response.send_message(f"Keyword: {keyword} added.")
    
    @app_commands.command(name="remove_spoiler_keyword")
    @app_commands.autocomplete(index=keyword_autocomplete)
    @app_commands.guild_only()
    async def remove_spoiler_keyword(self, interaction: discord.Interaction, index: str):
        keywords = get_spoiler_keywords()
        keyword_to_remove = keywords[int(index)]

        db_client[DB_NAME]["Spoiler Keywords"].delete_one({"keyword": keyword_to_remove})
        
        await interaction.response.send_message(f"Keyword removed.")

    @app_commands.command(name="add_spoiler_free_channel", description="Mark a channel as spoiler free.")
    async def add_spoiler_free_channel(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
            return
        
        if db_client[DB_NAME]["Spoiler Free Channels"].find_one({"channel_id": interaction.channel.id}): 
            await interaction.response.send_message(f"Channel already marked as spoiler free.")
            return

        db_client[DB_NAME]["Spoiler Free Channels"].insert_one({"channel_id": interaction.channel.id, "channel_name": interaction.channel.name})
        
        await interaction.response.send_message(f"Channel marked as spoiler free.")

    @app_commands.command(name="remove_spoiler_free_channel", description="Unmark a channel as spoiler free.")
    async def remove_spoiler_free_channel(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
            return
        
        if not db_client[DB_NAME]["Spoiler Free Channels"].find_one({"channel_id": interaction.channel.id}):
            await interaction.response.send_message(f"Channel not marked as spoiler free.")
            return

        db_client[DB_NAME]["Spoiler Free Channels"].delete_one({"channel_id": interaction.channel.id})
        
        await interaction.response.send_message(f"Channel unmarked as spoiler free.")
    
    
    async def check_spoiler(self, message: discord.Message) -> None:
        # Ignore messages from the bot itself to prevent potential loops
        if message.author.bot:
            return
        
        # List of keywords to look for
        keywords = get_spoiler_keywords()

        modlog_channel = self.bot.get_channel(MODLOG_CHANNEL_ID)

        # Get all from the collection "Spoiler Free Channels"
        current_channel_ids = get_spoiler_channel_ids()
        
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

def get_spoiler_channel_ids() -> List[int]:
    channels = []
    cursor = db_client[DB_NAME]["Spoiler Free Channels"].find({})
    for document in cursor:
        channels.append(document["channel_id"])
    return channels

def is_marked_spoiler(text, keyword) -> bool:
    pattern = rf'.*\|\|.*{re.escape(keyword)}.*\|\|.*'
    return re.search(pattern, text, re.DOTALL)


def get_spoiler_keywords() -> List[str]:
    keywords = []
    cursor = db_client[DB_NAME]["Spoiler Keywords"].find({})
    for document in cursor:
        keywords.append(document["keyword"])
    return keywords


def get_keyword_choices():
    choices = []
    for keyword in get_spoiler_keywords():
        choices.append(app_commands.Choice(name=keyword, value=keyword))
    return choices

async def setup(bot: commands.Bot) -> None: 
    await bot.add_cog(SpoilerCog(bot))