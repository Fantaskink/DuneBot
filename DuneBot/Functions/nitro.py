import discord
from discord import app_commands
from discord.ext import commands, tasks
from config import get_base_path
import os
import csv
import re

BOOSTER_CSV_PATH = get_base_path() + 'csv/boosters.csv'
PINGED_BOOSTER_CSV_PATH = get_base_path() + 'csv/pinged_boosters.csv'

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

        if is_new_booster(str(interaction.user.id)):
            # Create the role
            guild = self.bot.guilds[0]
            booster_role = await guild.create_role(name=role_name, color=role_color, reason="Booster role")
            await booster_role.edit(position=50)

            member = guild.get_member(interaction.user.id)

            # Add the role to the user
            await member.add_roles(booster_role, reason="Booster role")

            # Write first time server booster to CSV
            role_id = booster_role.id
            write_booster_to_csv(str(interaction.user.id), role_id)
            await interaction.response.send_message("Booster role assigned", ephemeral=True)
        else:
            # Get role id for existing server booster
            role_id = get_booster_role_id(str(interaction.user.id))
            booster_role = discord.utils.get(interaction.guild.roles, id=int(role_id))

            booster_role: discord.Role

            await booster_role.edit(name=role_name, color=role_color)

            await interaction.response.send_message("Booster role updated", ephemeral=True)
    

    async def handle_boosters(self) -> None:
        guild = self.bot.guilds[0]
        booster_ids = get_booster_ids() # ids of boosters with custom roles i.e., saved in csv file
        boosters = guild.premium_subscribers # List of all the server's boosters

        delete_removed_roles(self)

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
                    await user.remove_roles(role, reason="Booster role")
            
            # If the user has previously boosted and set up a custom role and has started boosting again
            if user in boosters:
                role_id = get_booster_role_id(user_id)
                role = discord.utils.get(guild.roles, id=int(role_id))

                if role not in user.roles:
                    await user.add_roles(role, reason="Booster role")


        # Ping users that do not have a custom role and have not been pinged already
        for booster in boosters:
            if not has_been_pinged(booster):
                general_chat = self.bot.guilds[0].get_channel(701674250591010840)
                general_chat: discord.TextChannel

                await general_chat.send(f"Thank you for boosting the server {booster.mention}! Use /get_booster_role to set up a custom role.")
                add_pinged_booster(booster)
    


    
    
def delete_removed_roles(self) -> None:
    # Open csv file, delete each row where the role id does not exist in the server
    with open(BOOSTER_CSV_PATH, 'r') as stats_file:
        csv_reader = csv.reader(stats_file)
        rows = list(csv_reader)

    with open(BOOSTER_CSV_PATH, 'w') as stats_file:
        csv_writer = csv.writer(stats_file)

        for row in rows:
            user_id = row[0]
            role_id = row[1]

            guild = self.bot.guilds[0]
            role = discord.utils.get(guild.roles, id=int(role_id))

            if role is not None:
                csv_writer.writerow([user_id, role_id])

def is_new_booster(user_id) -> bool:
    if not os.path.exists(BOOSTER_CSV_PATH) or os.path.getsize(BOOSTER_CSV_PATH) == 0:
        print("File is empty or doesn't exist")
        return True
    
    with open(BOOSTER_CSV_PATH, 'r') as stats_file:
        csv_reader = csv.reader(stats_file)

        for row in csv_reader:
            if row[0] == user_id:
                return False

        return True


def write_booster_to_csv(user_id, role_id) -> None:
    with open(BOOSTER_CSV_PATH, 'a') as booster_file:
        csv_writer = csv.writer(booster_file)

        # user_id, role_id
        csv_writer.writerow([user_id, role_id])
    return


def get_booster_role_id(user_id) -> str:
    with open(BOOSTER_CSV_PATH, 'r') as stats_file:
        csv_reader = csv.reader(stats_file)

        for row in csv_reader:
            if row[0] == user_id:
                return row[1]
        return None

def get_booster_ids() -> list[str]:
    booster_ids = []

    with open(BOOSTER_CSV_PATH, 'r') as stats_file:
        csv_reader = csv.reader(stats_file)

        for row in csv_reader:
            booster_ids.append(row[0])
    return booster_ids


def add_pinged_booster(user: discord.Member) -> None:
    with open(PINGED_BOOSTER_CSV_PATH, 'a') as csv_file:
        csv_file.write(str(user.id) + ",\n")


def has_been_pinged(user: discord.Member) -> bool:
    with open(PINGED_BOOSTER_CSV_PATH, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)

        for row in csv_reader:
            if row[0] == str(user.id):
                return True
        return False


async def setup(bot: commands.Bot) -> None: 
    await bot.add_cog(NitroCog(bot))