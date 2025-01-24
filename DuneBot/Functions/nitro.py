import discord
from discord import app_commands
from discord.ext import commands, tasks
from config import db_client, DB_NAME
import re

class NitroCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.handle_boosters_task.start()
    

    @tasks.loop(minutes=5)
    async def handle_boosters_task(self) -> None:
        await self.handle_boosters()    

    @app_commands.command(name="get_booster_role")
    @app_commands.describe(role_name="Type in the name of the role you wish to create.", hex_code="Type in the hex code of the color you wish the role to be.")
    @app_commands.guild_only()
    async def get_booster_role(self, interaction: discord.Interaction, role_name: str, hex_code: str) -> None:
        print(role_name, hex_code)
        # Terminate if the color is not a valid hex code
        if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', hex_code):
            await interaction.response.send_message("Hex code must be in format #xxxxxx", ephemeral=True)
            return
        
        if role_name == "everyone" or role_name == "here" or role_name == "Fedaykin" or role_name == "Naib" or role_name == "God Emperor":
            await interaction.response.send_message("Illegal role name", ephemeral=True)
            return
        
        guild = self.bot.guilds[0]
        member = guild.get_member(interaction.user.id)
        boosters = guild.premium_subscribers
        
        # Terminate if the user is not a server booster
        if member not in boosters:
            await interaction.response.send_message("You must be a server booster to run this command.", ephemeral=True)
            return
        
        # Convert the hex code to an integer
        role_color = discord.Colour(int(hex_code.replace("#", ""), 16))

        if is_new_booster(interaction.user.id):
            # Create the role
            guild = self.bot.guilds[0]
            booster_role = await guild.create_role(name=role_name, color=role_color, reason="Booster role")
            await booster_role.edit(position=50)

            member = guild.get_member(interaction.user.id)

            # Add the role to the user
            await member.add_roles(booster_role, reason="Booster role")

            # Write first time server booster to database
            role_id = booster_role.id
            user_id = interaction.user.id
            add_booster_to_db(user_id, role_id, role_name, hex_code)
            await interaction.response.send_message("Booster role assigned", ephemeral=True)
        else:
            # Get role id for existing server booster
            role_id = get_booster_role_id(interaction.user.id)
            booster_role = discord.utils.get(interaction.guild.roles, id=int(role_id))

            booster_role: discord.Role

            await booster_role.edit(name=role_name, color=role_color)

            await interaction.response.send_message("Booster role updated", ephemeral=True)
    

    async def handle_boosters(self) -> None:
        guild = self.bot.guilds[0]
        booster_ids = get_booster_ids() # ids of boosters with custom roles
        boosters = guild.premium_subscribers # List of all the server's boosters

        for user_id in booster_ids:
            user = guild.get_member(int(user_id))
        
            # If user has left the server, do nothing
            if user is None:
                continue
            
            # In cases where a user's boost has run out
            if user not in boosters:
                role_id = get_booster_role_id(user_id)
                role = discord.utils.get(guild.roles, id=int(role_id))

                if role is not None and role in user.roles:
                    await role.delete(reason="Boost expired")
            
            # If the user has previously boosted and set up a custom role and has started boosting again
            if user in boosters:
                # Create role again from database
                role_data = get_role_data(user_id)
                role_name = role_data["role_name"]
                role_color = discord.Colour(int(role_data["role_color"].replace("#", ""), 16))
                
                guild = self.bot.guilds[0]
                role = guild.create_role(name=role_name, color=role_color, reason="Booster role")

                await role.edit(position=50)

                member = guild.get_member(int(user_id))

                # Add the role to the user
                await member.add_roles(role, reason="Booster role")

                # Update the role id in the database
                db_client[DB_NAME]["Boosters"].update_one({"user_id": user_id}, {"$set": {"role_id": role.id}})


        # Ping users that do not have a custom role and have not been pinged already
        for booster in boosters:
            if not has_been_pinged(booster):
                general_chat = self.bot.guilds[0].get_channel(701674250591010840)
                general_chat: discord.TextChannel

                await general_chat.send(f"Thank you for boosting the server {booster.name}! Use ``/get_booster_role`` to set up a custom role.", )
                add_pinged_booster(booster)
    

def is_new_booster(user_id) -> bool:
    if db_client[DB_NAME]["Boosters"].find_one({"user_id": user_id}):
        return False
    return True
    

def add_booster_to_db(user_id, role_id, role_name, color_hex) -> None:
    db_client[DB_NAME]["Boosters"].insert_one({"user_id": user_id, "role_id": role_id, "role_name": role_name, "role_color": color_hex, "role_icon": None})


def get_booster_role_id(user_id) -> str:
    booster = db_client[DB_NAME]["Boosters"].find_one({"user_id": user_id})
    return booster["role_id"]

def get_booster_ids() -> list[str]:
    boosters = db_client[DB_NAME]["Boosters"].find()
    booster_ids = [booster["user_id"] for booster in boosters]
    return booster_ids


def add_pinged_booster(user: discord.Member) -> None:
    db_client[DB_NAME]["Pinged Boosters"].insert_one({"user_id": user.id})


def has_been_pinged(user: discord.Member) -> bool:
    if db_client[DB_NAME]["Pinged Boosters"].find_one({"user_id": user.id}):
        return True
    return False

def get_role_data(user_id) -> dict:
    return db_client[DB_NAME]["Boosters"].find_one({"user_id": user_id})

async def setup(bot: commands.Bot) -> None: 
    await bot.add_cog(NitroCog(bot))