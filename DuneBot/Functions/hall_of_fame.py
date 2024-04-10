import discord
from discord.ext import commands
from config import ENVIRONMENT

class HOFCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        ignored_channels = []

        channel_ids = {
            "production": {
                "hall_of_fame_channel": 1215786669337481277,
                "ignored_channels": [
                    1215786669337481277,  # Hall Of Fame channel
                    703342509488734289,  # Announcements
                    714440866886058054,  # Role Select
                    701681911348592771,  # Rules
                    701680471066542121,  # Welcome info
                ]
            },
            "development": {
                "hall_of_fame_channel": 1215775520520929374,
                "ignored_channels": [1215775520520929374]
            }
        }

        channels = channel_ids.get(ENVIRONMENT, {})
        hall_of_fame_channel = self.bot.get_channel(channels.get("hall_of_fame_channel"))
        ignored_channels = [self.bot.get_channel(id) for id in channels.get("ignored_channels", [])]

        reaction_channel = self.bot.guilds[0].get_channel(payload.channel_id)

        if reaction_channel is None:
            return

        reaction_message = await reaction_channel.fetch_message(payload.message_id)

        if reaction_message is None:
            return

        has_required_reactions = False

        for reaction in reaction_message.reactions:
            if isinstance(reaction.emoji, str):
                if reaction.count >= 10:
                    has_required_reactions = True
                    break
            elif reaction.emoji.name == "happyherbert" and reaction.count >= 5:
                has_required_reactions = True
                break
            elif reaction.count >= 10:
                has_required_reactions = True
                break
        
        if not has_required_reactions:
            return
        
        # Check if the message is in an ignored channel
        if reaction_channel in ignored_channels:
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

async def setup(bot: commands.Bot) -> None: 
    await bot.add_cog(HOFCog(bot))