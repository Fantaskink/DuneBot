import discord
from discord import app_commands
from discord.ext import commands
from discord.errors import NotFound
from config import db_client

happy_herbert_required_reactions = 5
required_reactions = 10

class HOFCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.hof_channel = self.get_hof_channel()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        tracked_channel_ids = []

        try:
            cursor = db_client["Tracked HOF Channels"].find({})
            for document in cursor:
                tracked_channel_ids.append(document["channel_id"])
        except Exception as e:
            print(f"Error fetching tracked channels: {e}")
            return

        try:
            hall_of_fame_channel_id = db_client["Hall of Fame Channel"].find_one({})["channel_id"]
        except Exception as e:
            print(f"Error fetching Hall of Fame channel: {e}")
            return

        if hall_of_fame_channel_id is None:
            return

        hall_of_fame_channel = self.bot.get_channel(hall_of_fame_channel_id)
        tracked_channels = [self.bot.get_channel(id) for id in tracked_channel_ids]

        reaction_channel = self.bot.guilds[0].get_channel(payload.channel_id)

        if reaction_channel is None:
            return

        try:
            reaction_message = await reaction_channel.fetch_message(payload.message_id)
        except NotFound:
            return

        if reaction_message is None:
            return

        has_required_reactions = False

        for reaction in reaction_message.reactions:
            if isinstance(reaction.emoji, str):
                if reaction.count >= required_reactions:
                    has_required_reactions = True
                    break
            elif reaction.emoji.name == "happyherbert" and reaction.count >= happy_herbert_required_reactions:
                has_required_reactions = True
                break
            elif reaction.count >= required_reactions:
                has_required_reactions = True
                break
        
        if not has_required_reactions:
            return
        
        # Check if the message is in a tracked channel
        if reaction_channel not in tracked_channels:
            return
        
        messages = [message async for message in hall_of_fame_channel.history(limit=100)]
        for message in messages:
            if message.embeds == []:
                continue
            message: discord.Message
            field = message.embeds[0].fields[0]
            jump_url_message_id = field.value.split('/')[-1]

            # Remove ')' from the end of the string
            jump_url_message_id = jump_url_message_id[:-1]
            if int(jump_url_message_id) == int(reaction_message.id):
                return

        # Create a new message in the hall of fame channel
        hof_embed = discord.Embed(description=reaction_message.content, color=discord.Colour.gold())
        hof_embed.set_author(name=reaction_message.author.display_name, icon_url=reaction_message.author.avatar.url)
        if reaction_message.attachments:
            hof_embed.set_image(url=reaction_message.attachments[0].url)
        hof_embed.add_field(name="Original", value=f"[Jump to message]({reaction_message.jump_url})")
        #hof_embed.set_footer(text=f"⭐ {reaction.count} | {reaction_channel.name}")

        await hall_of_fame_channel.send(embed=hof_embed)

        await reaction_channel.send(f"Post added to {hall_of_fame_channel.mention} {reaction_message.author.mention}")

    @app_commands.command(name="set_hof_tracked_channel", description="Add or remove a channel from the list of tracked channels.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.default_permissions(ban_members=True)
    async def set_tracked_channel(self, interaction: discord.Interaction) -> None:
        tracked_channel_ids = []

        try:
            cursor = db_client["Tracked HOF Channels"].find({})
            for document in cursor:
                tracked_channel_ids.append(document["channel_id"])
        except Exception as e:
            print(f"Error fetching tracked channels: {e}")
            return
        
        if interaction.channel.id in tracked_channel_ids:
            db_client["Tracked HOF Channels"].delete_one({"channel_id": interaction.channel.id})
            await interaction.response.send_message(f"Channel removed from tracked channels.")
        else:
            db_client["Tracked HOF Channels"].insert_one({"channel_id": interaction.channel.id})
            await interaction.response.send_message(f"Channel added to tracked channels.")

    def get_hof_channel(self) -> discord.TextChannel:
        try:
            hall_of_fame_channel_id = db_client["Hall of Fame Channel"].find_one({})["channel_id"]
        except Exception as e:
            print(f"Error fetching Hall of Fame channel: {e}")
            return None
        return self.bot.get_channel(hall_of_fame_channel_id)

async def setup(bot: commands.Bot) -> None: 
    await bot.add_cog(HOFCog(bot))