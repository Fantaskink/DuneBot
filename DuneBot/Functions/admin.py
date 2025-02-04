import discord
from discord import app_commands
from discord.ext import commands
from typing import List, Tuple
from config import MODLOG_CHANNEL_ID


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.deleted_messages: List[discord.Message] = []
        self.edited_messages: List[Tuple[discord.Message ,discord.Message]] = []
    
    def cog_unload(self) -> None:
        self.deleted_messages.clear()
        self.edited_messages.clear()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if payload.user_id == self.bot.user.id:
            return

        # Another Jules filter
        if payload.user.id == 443489357723074570 and payload.channel_id == 753460736579207208:
            await self.bot.http.remove_reaction(payload.channel_id, payload.message_id, payload.emoji, payload.user_id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        
        # Jules filter
        if message.channel.id == 753460736579207208 and message.author.id == 443489357723074570:
            await message.delete()
    
    
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        self.deleted_messages.append(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if before.author.bot:
            return
        self.edited_messages.append([before, after])

    @app_commands.command(name="snipe", description="Get deleted messages")
    @app_commands.describe(message_amount="Type in the amount of messages you wish to fetch.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.default_permissions(ban_members=True)
    async def snipe(self, interaction: discord.Interaction, message_amount: int = 1) -> None:
        """
        Retrieves a specified number of deleted messages and sends them in the modlogs channel
        """
        
        if self.deleted_messages == []:
            await interaction.response.send_message("No deleted messages", ephemeral=True)
            return
        
        modlog_channel = self.bot.get_channel(MODLOG_CHANNEL_ID)

        await interaction.response.send_message("Fetching deleted messages", ephemeral=True)
        
        for i in range(message_amount):
            try:
                message = self.deleted_messages.pop()
            except IndexError:
                break
            else:
                description = f"Message deleted in {message.channel.mention}"
                color = discord.Colour.gold()
                name = message.author.display_name
                icon_url = message.author.avatar.url

                embed = discord.Embed(color=color, description=description)
                embed.set_author(name=name, icon_url=icon_url)

                embed.add_field(name="Message", value=message.content, inline=False)
                await modlog_channel.send(embed=embed)
                for attachment in message.attachments:
                    await modlog_channel.send(attachment)
    

    @app_commands.command(name="editsnipe", description="Get edited messages")
    @app_commands.describe(message_amount="Type in the amount of messages you wish to fetch.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.default_permissions(ban_members=True)
    async def editsnipe(self, interaction: discord.Interaction, message_amount: int = 1) -> None:        
        if self.edited_messages == []:
            await interaction.response.send_message("No edited messages found", ephemeral=True)
            return
        
        modlog_channel = self.bot.get_channel(MODLOG_CHANNEL_ID)

        for i in range(message_amount):
            try:
                union = self.edited_messages.pop()
            except IndexError:
                break
            else:
                before, after = union
                if before.content == after.content:
                    continue
                description = f"Message edited in {before.channel.mention}"
                color = discord.Colour.gold()
                name = before.author.display_name
                icon_url = before.author.avatar.url

                embed = discord.Embed(color=color, description=description)
                embed.set_author(name=name, icon_url=icon_url)

                embed.add_field(name="Before", value=before.content, inline=False)
                embed.add_field(name="After", value=after.content, inline=False)
                await modlog_channel.send(embed=embed)
        
        await interaction.response.send_message(f"{message_amount} messages found. View in {modlog_channel.mention}", ephemeral=True)


    @app_commands.command(name="say", description="Make the bot say a message")
    @app_commands.describe(message="Type in the message you wish the bot to say.", message_id="Type in the id of the message you wish the bot to reply to.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.default_permissions(ban_members=True)
    async def say(self, interaction: discord.Interaction, message: str, message_id: str = None) -> None:
        """
        Command that takes a message as an argument and makes the bot say it. 
        Optional message link argument to make the bot reply to any message
        """
        
        await interaction.response.send_message("Alright boss", ephemeral=True)

        if message_id is not None:
            reply_message = await interaction.channel.fetch_message(message_id)
            await reply_message.reply(message)
        else:
            await interaction.channel.send(message)
        
        modlog_channel = self.bot.get_channel(MODLOG_CHANNEL_ID)

        description = f"Message sent in {interaction.channel.mention} by {interaction.user.mention}"
        embed = discord.Embed(color=discord.Colour.gold(), description=description)
        embed.add_field(name="Message", value=message, inline=False)

        await modlog_channel.send(embed=embed)
    

    @app_commands.command(name="sync", description="Sync commands")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.default_permissions(ban_members=True)
    async def sync(self, interaction: discord.Interaction) -> None:
        """
        Syncs commands to the Discord API
        """
        
        await interaction.response.send_message("Syncing commands", ephemeral=True)
        await self.bot.tree.sync()
    


async def setup(bot: commands.Bot) -> None: 
    await bot.add_cog(AdminCog(bot))