import discord
from discord import app_commands
from discord.ext import commands


class MiscCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    

    @app_commands.command(name="pfp")
    @app_commands.describe(user="Type in the name of the user whose profile picture you wish to see.")
    @app_commands.guild_only()
    async def pfp(self, interaction: discord.Interaction, user: discord.User):
        try:
            url = user.avatar.url
            await interaction.response.send_message(url)
        except:
            await interaction.response.send_message("This user has no profile picture.")


async def setup(bot: commands.Bot) -> None: 
    await bot.add_cog(MiscCog(bot))