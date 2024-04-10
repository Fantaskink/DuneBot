import discord
from discord import app_commands
from discord.ext import tasks
from discord.ext import commands
import random


class MiscCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.update_presence_task.start()
    

    @tasks.loop(hours=1)
    async def update_presence_task(self) -> None:
        quote = get_random_quote()
        activity = discord.CustomActivity(name=quote)
        await self.bot.change_presence(activity=activity)
    

    @app_commands.command(name="pfp")
    @app_commands.describe(user="Type in the name of the user whose profile picture you wish to see.")
    @app_commands.guild_only()
    async def pfp(self, interaction: discord.Interaction, user: discord.User) -> None:
        """Get the profile picture of a user."""
        try:
            url = user.avatar.url
            await interaction.response.send_message(url)
        except:
            await interaction.response.send_message("This user has no profile picture.")


def get_random_quote() -> str:
    quotes = [
        "The mystery of life isn't a problem to solve, but a reality to experience.",
        "What do you despise? By this are you truly known.",
        "There is no escape—we pay for the violence of our ancestors.",
        "Hope clouds observation.",
        "It is impossible to live in the past, difficult to live in the present and a waste to live in the future.",
        "The mind commands the body and it obeys. The mind orders itself and meets resistance.",
        "Without change something sleeps inside us, and seldom awakens. The sleeper must awaken.",
        "A process cannot be understood by stopping it. Understanding must move with the flow of the process, must join it and flow with it.",
        "Fear is the mind-killer.",
        "The people who can destroy a thing, they control it.",
        "Survival is the ability to swim in strange water.",
        "Arrakis teaches the attitude of the knife - chopping off what's incomplete and saying: 'Now, it's complete because it's ended here.'",
    ]

    return random.choice(quotes)


async def setup(bot: commands.Bot) -> None: 
    await bot.add_cog(MiscCog(bot))