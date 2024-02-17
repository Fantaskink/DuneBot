from typing import Optional
import discord
from discord import app_commands
from discord import ui
from discord.ext import commands
from discord.ext import tasks
from datetime import date, datetime, time, timedelta
import csv
import os
import re
from dotenv import load_dotenv, find_dotenv
from wordlegame import wordle_game

load_dotenv(find_dotenv())

intents = discord.Intents.all()
intents.message_content = True

global bot
bot = commands.Bot(command_prefix='!', intents=intents)

environment = os.environ.get("ENVIRONMENT")
print("Environment:", environment)

wordle_games = []

deleted_messages = []
edited_messages = []

base_path = ""

if environment == "production":
    base_path = '/home/ubuntu/DuneBot/DuneBot/'
elif environment == "development":
    base_path = 'DuneBot/'

@bot.event
async def on_ready():
    update_presence_task.start()
    handle_boosters_task.start()
    check_temp_msg_list_task.start()

    print(f'{bot.user} is now running.')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

@bot.event
async def on_message(message: discord.Message):
    await check_spoiler(message)
    await check_leak(message)

@bot.event
async def on_message_delete(message: discord.Message):
    # Check that author is not Dune bot
    if message.author.id == 1064478983095332864:
        return
    
    # Check that author's first role is not Thinking Machine
    if message.author.roles is not None:
        if message.author.roles[0].id == 701709720410652762: 
            return

    timestamped_msg = {
        "message": message,
        "timestamp": datetime.now()
    }

    deleted_messages.append(timestamped_msg)

    return

@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    # Check that author is not Dune bot and check that authors first role is not Thinking Machine
    if before.author.id == 1064478983095332864:
        return

    if before.author.roles is not None:
        if before.author.roles[0].id == 701709720410652762: 
            return
    
    if before.content == after.content:
        return
    
    timestamped_msg = {
        "before": before,
        "after": after,
        "timestamp": datetime.now()
    }
    
    edited_messages.append(timestamped_msg)
    return


@bot.tree.command(name="get_deleted_messages")
@app_commands.describe(minutes="Type in the number of minutes you wish to look back.")
async def get_deleted_messages(interaction: discord.Interaction, minutes: int):
    found_messages = []
    for deleted_message in deleted_messages:
        if datetime.now() - deleted_message["timestamp"] < timedelta(minutes=minutes):
            found_messages.append(deleted_message)
    
    if len(found_messages) == 0:
        await interaction.response.send_message("No deleted messages found", ephemeral=True)
        return
    
    if environment == "production":
        modlog_channel = bot.get_channel(701710310121275474) 
    elif environment == "development":
        modlog_channel = bot.get_channel(1131571647665672262)
    
    for found_message in found_messages:
        message: discord.Message = found_message["message"]
        description = f"Message deleted in {message.channel.mention}"
        color = discord.Colour.gold()
        name = message.author.display_name
        icon_url = message.author.avatar.url

        discord_embed = discord.Embed(color=color, description=description)
        discord_embed.set_author(name=name, icon_url=icon_url)

        discord_embed.add_field(name="Message", value=message.content, inline=False)
    
        await modlog_channel.send(embed=discord_embed, allowed_mentions=discord.AllowedMentions.none())
        for attachment in message.attachments:
            await modlog_channel.send(attachment)
    
    await interaction.response.send_message(f"{len(found_messages)} messages found. View in {modlog_channel.mention}", ephemeral=True)
    return

@bot.tree.command(name="get_edited_messages")
@app_commands.describe(minutes="Type in the number of minutes you wish to look back.")
async def get_edited_messages(interaction: discord.Interaction, minutes: int):
    found_messages = []
    for edited_message in edited_messages:
        if datetime.now() - edited_message["timestamp"] < timedelta(minutes=minutes):
            found_messages.append(edited_message)
    
    if len(edited_messages) == 0:
        await interaction.response.send_message("No edited messages found", ephemeral=True)
        return
    
    if environment == "production":
        modlog_channel = bot.get_channel(701710310121275474) 
    elif environment == "development":
        modlog_channel = bot.get_channel(1131571647665672262)
    
    for found_message in found_messages:
        before: discord.Message = found_message["before"]
        after: discord.Message = found_message["after"]
        description = f"Message edited in {before.channel.mention}"
        color = discord.Colour.gold()
        name = before.author.display_name
        icon_url = before.author.avatar.url

        discord_embed = discord.Embed(color=color, description=description)
        discord_embed.set_author(name=name, icon_url=icon_url)

        discord_embed.add_field(name="Old Message", value=before.content, inline=False)
        discord_embed.add_field(name="New Message", value=after.content, inline=False)
    
        await modlog_channel.send(embed=discord_embed, allowed_mentions=discord.AllowedMentions.none())
    
    await interaction.response.send_message(f"{len(found_messages)} messages found. View in {modlog_channel.mention}", ephemeral=True)
    return


async def check_spoiler(message: discord.Message):
    # Ignore messages from the bot itself to prevent potential loops
    if message.author == bot.user:
        return
    
    # List of keywords to look for
    keywords = await get_spoiler_keywords()
    
    if environment == "production":
        modlog_channel = bot.get_channel(701710310121275474)
        channel_ids = [
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
                   ]
    elif environment == "development":
        modlog_channel = bot.get_channel(1131571647665672262)
        channel_ids = [1130972092570009632] #test channel
    
    # Check if the message is from the desired channel
    for id in channel_ids:
        if message.channel.id == id:
            # Process the message for keywords
            for keyword in keywords:
                if keyword.lower() in message.content.lower() and not is_marked_spoiler(message.content.lower(), keyword.lower()):
                    await message.reply(f"Please be mindful of spoilers in this channel! Surround spoilers with '||' when discussing plot points from later books.")
                    await modlog_channel.send(f"Spoiler reminder sent in {message.channel.mention}, triggered by keyword: {keyword}.\nJump to message: {message.jump_url}")
                    break

    # Allow other event listeners (commands, etc.) to continue functioning
    await bot.process_commands(message)

async def check_leak(message):
    # Ignore messages from the bot itself to prevent potential loops
    if message.author == bot.user:
        return
    
    # List of keywords to look for
    keywords = await get_leak_keywords()
    
    if environment == "production":
        modlog_channel = bot.get_channel(701710310121275474)
        channel_ids = [702085230051328020, 864413789562470421, 1205108102370955264] 
    elif environment == "development":
        modlog_channel = bot.get_channel(1131571647665672262)
        channel_ids = [1205129588028473404] #test channel
    
    # Check if the message is not in a leak channel
    if message.channel.id not in channel_ids:
            # Process the message for keywords
            for keyword in keywords:
                if keyword.lower() in message.content.lower():
                    await message.reply(f"Do not post leaked details in this channel.")
                    await message.delete()
                    #await modlog_channel.send(f"Spoiler reminder sent in {message.channel.mention}, triggered by keyword: {keyword}.\nJump to message: {message.jump_url}")
                    break
        

    # Allow other event listeners (commands, etc.) to continue functioning
    await bot.process_commands(message)


async def get_spoiler_keywords():
    file_path = base_path + 'csv/keywords.csv'
    keywords = []

    with open(file_path, 'r', newline='') as csvfile:
        csv_reader = csv.reader(csvfile, skipinitialspace=False)

        for row in csv_reader:
            if row:
                keywords.append(row[0])
    return keywords


async def get_leak_keywords():
    file_path = base_path + 'csv/leak_words.csv'
    keywords = []

    with open(file_path, 'r', newline='') as csvfile:
        csv_reader = csv.reader(csvfile, skipinitialspace=False)

        for row in csv_reader:
            if row:
                keywords.append(row[0])
    return keywords


def is_marked_spoiler(text, keyword):
    pattern = rf'.*\|\|.*{re.escape(keyword)}.*\|\|.*'
    return re.search(pattern, text, re.DOTALL)


async def update_presence():
    days_until_string = await get_days_until_string("2024-03-01", "00:00")

    #days_until_string = "ITS FUCKING DELAYED"

    activity = discord.CustomActivity(name=days_until_string)
    await bot.change_presence(activity=activity)

async def check_temp_msg_list():
    counter = 0
    for deleted_message in deleted_messages:
        if datetime.now() - deleted_message["timestamp"] > timedelta(minutes=600):
            deleted_messages.remove(deleted_message)
            counter += 1
    for edited_message in edited_messages:
        if datetime.now() - edited_message["timestamp"] > timedelta(minutes=600):
            edited_messages.remove(edited_message)
            counter += 1
    print(f"{counter} cached messages removed from memory.")
    return
    

@tasks.loop(hours=24)
async def update_presence_task():
    await update_presence()
    

@tasks.loop(hours=12)
async def handle_boosters_task():
    await handle_boosters()

@tasks.loop(hours=1)
async def check_temp_msg_list_task():
    await check_temp_msg_list()

async def get_days_until_string(target_date_str, time_str):
    # Get the current date
    today = datetime.now()

    # Parse the target date and time from the input strings
    target_date = date.fromisoformat(target_date_str)
    target_time = time.fromisoformat(time_str)

    # Combine the target date and time into a single datetime object
    target_datetime = datetime.combine(target_date, target_time)

    # Calculate the time difference between the target datetime and the current datetime
    delta = target_datetime - today

    days_until = delta.days

    if days_until == 1:
        return(f"{days_until} day until Dune Part Two")
        
    if days_until <= 0:
        return(f"Dune Part Two OUT NOW!")
    
    return(f"{days_until} days until Dune Part Two")

@bot.tree.command(name="print_spoiler_keywords")
@app_commands.describe()
async def print_spoiler_keywords(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
        return

    keywords = await get_spoiler_keywords()
    keyword_string = ""
    for keyword in keywords:
        keyword_string = keyword_string + (str(keywords.index(keyword)) + ":" + keyword + "\n")

    await interaction.response.send_message("```" + keyword_string + "```")

@bot.tree.command(name="print_leak_keywords")
@app_commands.describe()
async def print_leak_keywords(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
        return

    keywords = await get_leak_keywords()
    keyword_string = ""
    for keyword in keywords:
        keyword_string = keyword_string + (str(keywords.index(keyword)) + ":" + keyword + "\n")

    await interaction.response.send_message("```" + keyword_string + "```", ephemeral=True)


@bot.tree.command(name="add_spoiler_keyword")
@app_commands.describe(keyword="Type in a keyword you wish to be considered a spoiler.")
async def add_spoiler_keyword(interaction: discord.Interaction, keyword: str):

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
        return
    
    file_path = base_path + 'csv/keywords.csv'

    with open(file_path, 'a') as csv_file:
            csv_file.write(keyword + ",\n")
    
    await interaction.response.send_message(f"Keyword: {keyword} added.")

@bot.tree.command(name="add_leak_keyword")
@app_commands.describe(keyword="Type in a keyword you wish to be considered a leak.")
async def add_leak_keyword(interaction: discord.Interaction, keyword: str):

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
        return
    
    file_path = base_path + 'csv/leak_words.csv'

    with open(file_path, 'a') as csv_file:
            csv_file.write(keyword + ",\n")
    
    await interaction.response.send_message(f"Keyword: {keyword} added.", ephemeral=True)


@bot.tree.command(name="delete_spoiler_keyword")
@app_commands.describe(index="Type in the index of the spoiler keyword you wish to remove.")
async def delete_spoiler_keyword(interaction: discord.Interaction, index: int):

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
        return

    file_path = base_path + 'csv/keywords.csv'

    with open(file_path, 'r', newline='') as csv_file:
        reader = csv.reader(csv_file)
        data = list(reader)

    # Check if the row_index is valid
    if index < 0 or index >= len(data):
        await interaction.response.send_message("Invalid index", ephemeral=True)
        return
    
    # Remove the desired row
    data.pop(index)

    # Write the modified data back to the CSV file
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)
    
    await interaction.response.send_message(f"Keyword removed.")

@bot.tree.command(name="delete_leak_keyword")
@app_commands.describe(index="Type in the index of the leak keyword you wish to remove.")
async def delete_leak_keyword(interaction: discord.Interaction, index: int):

    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
        return

    file_path = base_path + 'csv/leak_words.csv'

    with open(file_path, 'r', newline='') as csv_file:
        reader = csv.reader(csv_file)
        data = list(reader)

    # Check if the row_index is valid
    if index < 0 or index >= len(data):
        await interaction.response.send_message("Invalid index", ephemeral=True)
        return
    
    # Remove the desired row
    data.pop(index)

    # Write the modified data back to the CSV file
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)
    
    await interaction.response.send_message(f"Keyword removed.")

@bot.tree.command(name="meme")
@app_commands.describe(top_text="Top text", bottom_text="Bottom text", image_link="Image link")
async def meme(interaction: discord.Interaction, top_text: str, bottom_text: str, image_link: str):
    from PIL import Image, ImageDraw, ImageFont
    import requests
    from io import BytesIO

    await interaction.response.defer(ephemeral=True)
    
    # Load the image from the link
    response = requests.get(image_link)
    img = Image.open(BytesIO(response.content))

    file_path = base_path + 'impact.tff'

    # Load Impact font
    font = ImageFont.truetype(file_path, 40)  # Make sure you have the "impact.ttf" file in the same directory

    # Initialize the drawing context
    draw = ImageDraw.Draw(img)

    # Calculate text bounding boxes
    top_text_bbox = draw.textbbox((0, 0), top_text, font=font)
    bottom_text_bbox = draw.textbbox((0, 0), bottom_text, font=font)

    # Calculate text positions
    width, height = img.size
    top_text_position = ((width - top_text_bbox[2]) / 2, 10)
    bottom_text_position = ((width - bottom_text_bbox[2]) / 2, height - bottom_text_bbox[3] - 10)

    # Draw top and bottom text on the image
    draw.text(top_text_position, top_text, fill="white", font=font)
    draw.text(bottom_text_position, bottom_text, fill="white", font=font)

    # Save the modified image to a BytesIO object
    modified_img_io = BytesIO()
    img.save(modified_img_io, format="PNG")
    modified_img_io.seek(0)

    # Create a Discord File object
    modified_img_file = discord.File(modified_img_io, filename="meme.png")

    await interaction.followup.send(file=modified_img_file)


# Command that fetches the profile picture of a user and sends it as a message
@bot.tree.command(name="pfp")
@app_commands.describe(user="Type in the name of the user whose profile picture you wish to see.")
async def pfp(interaction: discord.Interaction, user: discord.User):
    await interaction.response.send_message(user.avatar.url)


# Command that takes a message as an argument and makes the bot say it. Optional message link argument to make the bot reply to any message
@bot.tree.command(name="say")
@app_commands.describe(message="Type in the message you wish the bot to say.", message_id="Type in the id of the message you wish the bot to reply to.")
async def say(interaction: discord.Interaction, message: str, message_id: str = None):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
        return
    
    await interaction.response.send_message("Alright boss", ephemeral=True)

    if message_id is not None:
        channel = interaction.channel
        reply_message = await channel.fetch_message(message_id)
        await reply_message.reply(message)
    else:
        channel = interaction.channel
        await channel.send(message)


async def get_wordle_games():
    global wordle_games
    return wordle_games


async def get_wordle_game(user_id):
    global wordle_games
    for wordle_game in wordle_games:
        if wordle_game.get_user_id() == user_id:
            return wordle_game
    return None


async def add_wordle_game(wordle_game):
    global wordle_games
    wordle_games.append(wordle_game)


async def remove_wordle_game(wordle_game):
    global wordle_games
    wordle_games.remove(wordle_game)


async def get_valid_guesses():
    file_path = base_path + 'wordle/valid_guesses.csv'
    with open(file_path, 'r') as f:
        valid_guesses = f.read().splitlines()
        return valid_guesses


async def get_all_solutions():
    file_path = base_path + 'wordle/valid_solutions.csv'
    with open(file_path, 'r') as f:
        valid_solutions = f.read().splitlines()
        return valid_solutions


@bot.tree.command(name="wordle")
@app_commands.describe(dune_mode="Choose yes to play wordle with terms and names from Dune. Choose no to play with standard words.")
async def wordle(interaction: discord.Interaction, dune_mode: bool):
    game_in_progress = await get_wordle_game(interaction.user.id)

    if game_in_progress is None:
        new_game = wordle_game(interaction.user.id, dune_mode)
        await add_wordle_game(new_game)
        length = new_game.get_word_length()
        await interaction.response.send_message(f"Wordle game started. \n Guess a {length} letter word with /guess", ephemeral=True)
    else:
        await interaction.response.send_message("You already have a wordle game in progress", ephemeral=True)


@bot.tree.command(name="guess")
@app_commands.describe(guess="Type in the word you wish to guess.")
async def guess(interaction: discord.Interaction, guess: str):
    await interaction.response.defer(ephemeral=True)

    guess = guess.lower().strip()
    game = await get_wordle_game(interaction.user.id)

    if game is None:
        await interaction.followup.send("You do not have a wordle game in progress")
        return
    
    if len(guess) != game.get_word_length():
        length = game.get_word_length()
        await interaction.followup.send(f"Guess must be {length} letters long")
        return

    # If guess contains non-alphabetical characters
    if not guess.isalpha():
        await interaction.followup.send("Guess must contain only letters")
        return
    
    if not game.is_dune_mode():
        valid_guesses = await get_valid_guesses()
        solutions = await get_all_solutions()
        if guess not in valid_guesses and guess not in solutions:
            await interaction.followup.send("Not a word")
            return
    
    result_string = await check_guess(guess, game)

    await interaction.channel.send(interaction.user.display_name + " guessed: " + guess.upper())

    await interaction.channel.send(result_string)

    if guess == game.get_word():
        await interaction.followup.send("You win!")
        await end_wordle_game(interaction.user.id)
        await player_win_game(str(interaction.user.id))
        return
    
    discarded_letters = game.get_discarded_letters()
    discarded_letters_list = list(discarded_letters)  # Convert the set to a list
    discarded_letters_string = ""

    last_item = discarded_letters_list[-1]
    for element in discarded_letters_list:
        if element == last_item:
            discarded_letters_string += element
        else:
            discarded_letters_string += element + ", "

    await interaction.channel.send("Discarded letters: " +  discarded_letters_string)
    
    game.subtract_guess()

    await interaction.channel.send("Guesses left: " + str(game.get_guesses_left()))

    if game.get_guesses_left() == 0:
        await interaction.channel.send("You lose!")
        await interaction.channel.send("The word was: " + game.get_word().upper())
        await end_wordle_game(interaction.user.id)
        await interaction.followup.send("Play again with /wordle")
        await player_lose_game(str(interaction.user.id))
        return
    
    await interaction.followup.send("Guess again with /guess")
    return


async def check_guess(guess, game: wordle_game):
    solution = game.get_word()
    solution_length = game.get_word_length()
    output = ["_" for _ in range(solution_length)]
    letters = list(solution)

    for i in range(0, solution_length):
        if guess[i] == solution[i]:
            output[i] = "🟩"
            if guess[i] in letters:
                letters.remove(guess[i])

        elif guess[i] in solution and guess[i] in letters:
            output[i] = "🟨"
            if guess[i] in letters:
                letters.remove(guess[i])
        else:
            output[i] = "⬜"
            if guess[i] not in solution:
                game.update_discarded_letters(guess[i])

    output_string = "".join(output)

    return output_string

async def end_wordle_game(user_id: discord.User.id):
    wordle_game = await get_wordle_game(user_id)
    await remove_wordle_game(wordle_game)
    

async def player_in_stats(user_id):
    file_path = base_path + 'wordle/player_stats.csv'

    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        print("File is empty or doesn't exist")
        return False
    
    with open(file_path, 'r') as stats_file:
        csv_reader = csv.reader(stats_file)

        for row in csv_reader:
            if row[0] == user_id:
                return True

        return False
    

async def player_win_game(user_id):
    # If player is not in stats.csv, add them
    if not await player_in_stats(str(user_id)):
        await add_player_to_stats(user_id)
    
    # Update stats.csv and add 1 to second column
    with open(base_path + 'wordle/player_stats.csv', 'r') as stats_file:
        csv_reader = csv.reader(stats_file)
        lines = list(csv_reader)
        for i in range(len(lines)):
            if lines[i][0] == user_id:
                lines[i][1] = int(lines[i][1]) + 1
    
    # Write to stats.csv
    with open(base_path + 'wordle/player_stats.csv', 'w') as stats_file:
        csv_writer = csv.writer(stats_file)
        csv_writer.writerows(lines)


async def player_lose_game(user_id):
    # If player is not in stats.csv, add them
    if not await player_in_stats(user_id):
        await add_player_to_stats(user_id)
    
    # Update stats.csv and add 1 to third column
    with open(base_path + 'wordle/player_stats.csv', 'r') as stats_file:
        csv_reader = csv.reader(stats_file)
        lines = list(csv_reader)
        for i in range(len(lines)):
            if lines[i][0] == user_id:
                lines[i][2] = int(lines[i][2]) + 1
    
    # Write to stats.csv
    with open(base_path + 'wordle/player_stats.csv', 'w') as stats_file:
        csv_writer = csv.writer(stats_file)
        csv_writer.writerows(lines)


async def add_player_to_stats(user_id):
    with open(base_path + 'wordle/player_stats.csv', 'a') as stats_file:
        csv_writer = csv.writer(stats_file)
        csv_writer.writerow([user_id, 0, 0])


async def get_wins(user_id):
    with open(base_path + 'wordle/player_stats.csv', 'r') as stats_file:
        csv_reader = csv.reader(stats_file)

        for row in csv_reader:
            if row[0] == user_id:
                return row[1]


async def get_losses(user_id):
    with open(base_path + 'wordle/player_stats.csv', 'r') as stats_file:
        csv_reader = csv.reader(stats_file)

        for row in csv_reader:
            if row[0] == user_id:
                return row[2]


async def get_win_percentage(user_id):
    with open(base_path + 'wordle/player_stats.csv', 'r') as stats_file:
        csv_reader = csv.reader(stats_file)

        for row in csv_reader:
            if row[0] == user_id:
                if int(row[1]) + int(row[2]) == 0:
                    return 0
                else:
                    return round(int(row[1]) / (int(row[1]) + int(row[2])) * 100, 2)


@bot.tree.command(name="wordle_player_stats")
@app_commands.describe(player="Type in the name of the player whose stats you wish to see.")
async def wordle_player_stats(interaction: discord.Interaction, player: discord.User):
    if await player_in_stats(str(player.id)):
        wins = await get_wins(str(player.id))
        losses = await get_losses(str(player.id))
        win_rate = await get_win_percentage(str(player.id))
        await interaction.response.send_message(f"{player.display_name} has {wins} wins and {losses} losses.\n Win rate: {win_rate}%")
    else:
        await interaction.response.send_message(f"{player.display_name} has not played any wordle games")


@bot.tree.command(name="kino")
@app_commands.describe(movie_title="Type in the name of the movie you wish to look up.", year="Type in the year the movie was released.")
async def kino(interaction: discord.Interaction, movie_title: str, year: str):
    await interaction.response.defer()
    from media_fetcher import fetch_movie_data
    from primarycolor import get_primary_hex_color

    movie_data = fetch_movie_data(movie_title, year)

    if movie_data is None:
        await interaction.followup.send("Movie not found")

    if movie_data['Poster'] == 'N/A':
        color_hex = discord.Colour.blue()
    else:
        color_hex = get_primary_hex_color(movie_data['Poster'])

    title = movie_data['Title'] + " (" + movie_data['Year'] + ")"

    movie_link = f"https://www.imdb.com/title/{movie_data['imdbID']}"

    discord_embed = discord.Embed(title=title, url=movie_link, color=color_hex)
    
    if movie_data['Poster'] != 'N/A':
        thumbnail_url = movie_data['Poster']
        discord_embed.set_thumbnail(url=thumbnail_url)

    discord_embed.add_field(name='Director', value=movie_data['Director'], inline=False)
    discord_embed.add_field(name='Genre', value=movie_data['Genre'], inline=True)
    discord_embed.add_field(name='Runtime', value=movie_data['Runtime'], inline=True)
    discord_embed.add_field(name='Description', value=movie_data['Plot'], inline=False)
    discord_embed.add_field(name='IMDb Rating', value=movie_data['imdbRating'], inline=True)

    rotten_tomatoes_score = None
    for rating in movie_data['Ratings']:
        if rating['Source'] == 'Rotten Tomatoes':
            rotten_tomatoes_score = rating['Value']


    discord_embed.add_field(name='Rotten Tomatoes Score', value=rotten_tomatoes_score, inline=True)
    discord_embed.add_field(name='Metacritic Score', value=movie_data['Metascore'], inline=True)
    discord_embed.add_field(name='Box Office', value=movie_data['BoxOffice'], inline=False)

    await interaction.followup.send(embed=discord_embed)


@bot.tree.command(name="book")
@app_commands.describe(book_title="Type in the name of the book you wish to look up.")
async def book(interaction: discord.Interaction, book_title: str):
    await interaction.response.defer()
    from media_fetcher import fetch_book_data
    from primarycolor import get_primary_hex_color

    data = fetch_book_data(book_title)

    if data is None:
        await interaction.followup.send("Book not found")
        return

    title = data['title']
    author = data['author']
    rating = data['rating'] + "/5"
    thumbnail_url = data['thumbnail_url']
    page_count = data['page_count'][0]
    publish_date = data['publish_date'][0]
    book_link = data['book_link']


    if 'description' not in data:
        long_description = "No description available"
    else:
        long_description = data['description']
        short_description = (long_description[:500] + '...') if len(long_description) > 75 else long_description
    
    color_hex = get_primary_hex_color(thumbnail_url)    

    discord_embed = discord.Embed(title=title, url=book_link, color=color_hex)

    discord_embed.set_thumbnail(url=thumbnail_url)

    discord_embed.add_field(name='Authors', value=author, inline=True)
    discord_embed.add_field(name='Published', value=publish_date, inline=True)
    discord_embed.add_field(name='Description', value=short_description, inline=False)
    discord_embed.add_field(name='Page Count', value=page_count, inline=True)
    discord_embed.add_field(name='Rating', value=rating, inline=True)

    await interaction.followup.send(embed=discord_embed)


def get_title_from_index(index):
    match (index):
        case (1):
            return "Dune"
        case (2):
            return "Dune Messiah"
        case (3):
            return "Children of Dune"
        case (4):
            return "God Emperor of Dune"
        case (5):
            return "Heretics of Dune"
        case (6):
            return "Chapterhouse Dune"
        case (_):
            return "Unknown"


class SearchResultView(discord.ui.View):
    def __init__(self, data, search_term):
        super().__init__()
        self.data = data
        self.search_term = search_term
        self.current_page = 1
        self.timeout = 600
    
    async def send(self, interaction: discord.Interaction):
        self.message = await interaction.followup.send(view=self)
        await self.update_message(self.data[self.current_page - 1])

    def create_embed(self, data: dict):
        embed = discord.Embed(title=f"Search Result Page {self.current_page} of {len(self.data)}", color=discord.Colour.dark_gold())
        title = get_title_from_index(data["book_number"])
        embed.add_field(name="Found in", value=title, inline=False)

        result = data["results"]

        result = re.sub(f'({self.search_term})', r'***\1***', result, flags=re.IGNORECASE)

        if data["book_number"] == 1:
            embed.add_field(name="Excerpt", value=result, inline=False)
        else:
            embed.add_field(name="Excerpt", value=f"||{result}||", inline=False)
        
        return embed
    
    def update_buttons(self):
        if self.current_page == 1:
            self.first_page_button.disabled = True
            self.prev_button.disabled = True
            self.first_page_button.style = discord.ButtonStyle.gray
            self.prev_button.style = discord.ButtonStyle.gray
        else:
            self.first_page_button.disabled = False
            self.prev_button.disabled = False
            self.first_page_button.style = discord.ButtonStyle.green
            self.prev_button.style = discord.ButtonStyle.primary

        if self.current_page == len(self.data):
            self.next_button.disabled = True
            self.last_page_button.disabled = True
            self.last_page_button.style = discord.ButtonStyle.gray
            self.next_button.style = discord.ButtonStyle.gray
        else:
            self.next_button.disabled = False
            self.last_page_button.disabled = False
            self.last_page_button.style = discord.ButtonStyle.green
            self.next_button.style = discord.ButtonStyle.primary
    
    async def on_timeout(self):
        self.first_page_button.disabled = True
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.last_page_button.disabled = True
        self.clear_items()
        self.stop()

        await self.update_message(self.data[self.current_page - 1])


    @discord.ui.button(label="|<", style=discord.ButtonStyle.primary)
    async def first_page_button(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.defer()
        self.current_page = 1
        await self.update_message(self.data[self.current_page - 1])

    @discord.ui.button(label="<", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.defer()
        self.current_page -= 1
        await self.update_message(self.data[self.current_page - 1])

    @discord.ui.button(label=">", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.defer()
        self.current_page += 1
        await self.update_message(self.data[self.current_page - 1])

    @discord.ui.button(label=">|", style=discord.ButtonStyle.primary)
    async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.defer()
        self.current_page = len(self.data)
        await self.update_message(self.data[self.current_page - 1])

    
    async def update_message(self, data):
        self.update_buttons()
        await self.message.edit(embed=self.create_embed(data), view=self)
        


@bot.tree.command(name="search_in_dune")
@app_commands.describe(search_term="Type in the string you wish to search for.")
async def search_in_dune(interaction: discord.Interaction, search_term: str):
    await interaction.response.defer()

    if len(search_term) < 3:
        await interaction.followup.send("Search term must be at least 3 characters long")
        return

    from media_fetcher import search_in_epub_with_element

    results = []

    results.append(search_in_epub_with_element(search_term, 1, 'p'))
    results.append(search_in_epub_with_element(search_term, 2, 'div'))
    results.append(search_in_epub_with_element(search_term, 3, 'p'))
    results.append(search_in_epub_with_element(search_term, 4, 'p'))
    results.append(search_in_epub_with_element(search_term, 5, 'p'))
    results.append(search_in_epub_with_element(search_term, 6, 'div'))

    results = [result for result in results if result is not None]

    from itertools import chain

    flattened_results = list(chain(*results))

    if len(results) == 0:
        await interaction.followup.send("No results found")
        return

    search_view = SearchResultView(flattened_results, search_term)

    await search_view.send(interaction)


async def is_new_booster(user_id):
    file_path = base_path + 'csv/boosters.csv'

    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        print("File is empty or doesn't exist")
        return True
    
    with open(file_path, 'r') as stats_file:
        csv_reader = csv.reader(stats_file)

        for row in csv_reader:
            if row[0] == user_id:
                return False

        return True


async def write_booster_to_csv(user_id, role_id):
    with open(base_path + 'csv/boosters.csv', 'a') as booster_file:
        csv_writer = csv.writer(booster_file)

        # user_id, role_id, is_currently_boosting
        csv_writer.writerow([user_id, role_id, True])
    return


async def get_booster_role_id(user_id):
    file_path = base_path + 'csv/boosters.csv'

    with open(file_path, 'r') as stats_file:
        csv_reader = csv.reader(stats_file)

        for row in csv_reader:
            if row[0] == user_id:
                return row[1]
        return None

async def get_booster_ids():
    file_path = base_path + 'csv/boosters.csv'
    booster_ids = []

    with open(file_path, 'r') as stats_file:
        csv_reader = csv.reader(stats_file)

        for row in csv_reader:
            booster_ids.append(row[0])
    return booster_ids

async def set_booster_status(user_id, status): # True if boosting, False if not
    file_path = base_path + 'csv/boosters.csv'

    with open(file_path, 'r') as stats_file:
        csv_reader = csv.reader(stats_file)
        lines = list(csv_reader)
        for i in range(len(lines)):
            if lines[i][0] == user_id:
                lines[i][2] = status
    
    with open(file_path, 'w') as stats_file:
        csv_writer = csv.writer(stats_file)
        csv_writer.writerows(lines)

async def is_active_booster(user_id):
    file_path = base_path + 'csv/boosters.csv'

    with open(file_path, 'r') as stats_file:
        csv_reader = csv.reader(stats_file)

        for row in csv_reader:
            if row[0] == user_id:
                return row[2]
        return False

@bot.tree.command(name="get_booster_role")
@app_commands.describe(role_name="Type in the name of the role you wish to create.", hex_code="Type in the hex code of the color you wish the role to be.")
async def get_booster_role(interaction: discord.Interaction, role_name: str, hex_code: str):
    print(role_name, hex_code)
    # Terminate if the color is not a valid hex code
    if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', hex_code):
        await interaction.response.send_message("Hex code must be in format #xxxxxx", ephemeral=True)
        return
    
    guild = bot.guilds[0]
    member = guild.get_member(interaction.user.id)
    boosters = guild.premium_subscribers
    
    # Terminate if the user is not a server booster
    if member not in boosters:
        await interaction.response.send_message("You must be a server booster to run this command.", ephemeral=True)
        return
    
    # Convert the hex code to an integer
    role_color = discord.Colour(int(hex_code.replace("#", ""), 16))

    if await is_new_booster(str(interaction.user.id)):
        # Create the role
        guild = interaction.guild
        booster_role = await guild.create_role(name=role_name, color=role_color, reason="Booster role")

        # Add the role to the user
        await interaction.user.add_roles(booster_role, reason="Booster role")

        # Write first time server booster to CSV
        role_id = booster_role.id
        await write_booster_to_csv(str(interaction.user.id), role_id)
        await interaction.response.send_message("Booster role assigned", ephemeral=True)
    else:
        # Get role id for existing server booster
        role_id = await get_booster_role_id(str(interaction.user.id))
        booster_role = discord.utils.get(interaction.guild.roles, id=int(role_id))

        booster_role: discord.Role

        await booster_role.edit(name=role_name, color=role_color)

        await interaction.response.send_message("Booster role updated", ephemeral=True)


async def handle_boosters():
    booster_ids = await get_booster_ids() # ids of boosters with custom roles i.e., saved in csv file
    boosters = bot.guilds[0].premium_subscribers # List of all the server's boosters

    for user_id in booster_ids:
        user = bot.guilds[0].get_member(int(user_id))
        
        user: discord.Member

        # If user has left the server, do nothing
        if user is None:
            break
        
        # In cases where a user's boost has run out
        if user not in boosters:
            role_id = await get_booster_role_id(id)
            guild = bot.guilds[0]
            role = discord.utils.get(guild.roles, id=int(role_id))

            user.remove_roles(role, reason="Booster role")

            await set_booster_status(id, False)
        
        # If the user has previously boosted and set up a custom role and has started boosting again
        if await is_active_booster(id) == "False" and user in boosters:
            role_id = await get_booster_role_id(user_id)
            guild = bot.guilds[0]
            role = discord.utils.get(guild.roles, id=int(role_id))

            user.add_roles(role, reason="Booster role")

            await set_booster_status(id, True)
    
    # Ping users that do not have a custom role and have not been pinged already
    for booster in boosters:
        booster: discord.Member
        if not await has_been_pinged(booster):
            await booster.send("Thank you for boosting the server! Use /get_booster_role to set up a custom role.")
            await add_pinged_booster(booster)


async def add_pinged_booster(user: discord.Member):
    filepath = base_path + 'csv/pinged_boosters.csv'

    with open(filepath, 'a') as csv_file:
        csv_file.write(str(user.id) + ",\n")


async def has_been_pinged(user: discord.Member):
    filepath = base_path + 'csv/pinged_boosters.csv'

    with open(filepath, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)

        for row in csv_reader:
            if row[0] == str(user.id):
                return True
        return False

'''

@bot.tree.command(name="add_existing_booster")
@app_commands.describe(user="Type in the name of the user you wish to add as a booster.", role_id="Type in the id of the role you wish to assign to the user.")
async def add_existing_booster(interaction: discord.Interaction, user: discord.User, role_id: str):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
        return
    user: discord.Member

    await write_booster_to_csv(str(user.id), role_id)
    await interaction.response.send_message("Booster role assigned", ephemeral=True)

# Set up subreddit streaming in specific channel
@bot.tree.command(name="stream_subreddit")
@app_commands.describe(subreddit="Type the name of the subreddit you wish to stream content from.")
async def set_subreddit_stream_channel(interaction: discord.Interaction, subreddit: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
    else:
        # Get channel command was run in
        ctx = await bot.get_context(interaction)

        # Store channel and specified subreddit in database if subreddit exists
        if await reddit.check_subreddit_exists(subreddit):
            database.add_subreddit(ctx.channel.id, subreddit)
            # Send confirmation message
            await interaction.response.send_message(f"Channel now streaming submissions from r/{subreddit}")
        else:
            await interaction.response.send_message(f"r/{subreddit} does not exist")


@bot.tree.command(name="stop_stream")
@app_commands.describe()
async def stop_subreddit_stream_channel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You are not authorized to run this command.", ephemeral=True)
    else:
        # Get channel command was run in
        ctx = await bot.get_context(interaction)
        channel_id = ctx.channel.id

        subreddits = database.get_all_documents("DuneBot", "subreddits")

        found = False

        for subreddit in subreddits:
            if channel_id == subreddit["channel_id"]:
                found = True

        if found:
            database.delete_subreddit_by_channel_id(channel_id)
            await interaction.response.send_message("Subreddit stream stopped")
        else:
            await interaction.response.send_message("No subreddit stream active in channel")


@tasks.loop(seconds=10)  # repeat after every 10 seconds
async def loop():
    #print("Loop")
    verify_channels()
    task = asyncio.create_task(start_streams())
    shield_task = asyncio.shield(task)


async def start_streams():
    documents = database.get_all_documents("DuneBot", "subreddits")

    # Begins a stream for any document with "is_active" set to false, then sets the value to true
    for document in documents:
        if not document["is_active"]:
            channel_id = document["channel_id"]
            channel = bot.get_channel(int(channel_id))
            subreddit = document["subreddit"]
            database.set_activity_status(document["_id"], True)
            print("Beginning stream for:", subreddit, "in", bot.get_channel(int(channel_id)))
            await reddit.stream_subreddit(channel_id, channel, subreddit)
            print("stream function terminated")
            database.set_activity_status(document["_id"], False)


# Delete database document if its channel_id does not match a channel on the server
def verify_channels():
    documents = database.get_all_documents("DuneBot", "subreddits")

    for document in documents:
        channel_id = document["channel_id"]
        channel = bot.get_channel(int(channel_id))
        if channel is None:
            database.delete_subreddit(document["_id"])


@bot.tree.command(name="encyclopedia")
@app_commands.describe(keyword="Type in the name of the entry you wish to look up.")
async def encyclopedia(interaction: discord.Interaction, keyword: str):
    file_path = base_path + 'csv/encyclopedia.csv'

    with open(file_path, 'r', newline='') as csvfile:
        csv_reader = csv.reader(csvfile, skipinitialspace=False)

        for row in csv_reader:
            if row:
                if row[0].lower() == keyword.lower():
                    page_count = len(row) - 1
                    view = Pages(page_count)
                    await interaction.response.send_message(row[1], view=view)
                    await view.wait()
                    if view.index is None:
                        await interaction.response.edit_message(view=view)
                    elif view.index:
                        print("index" + str(view.index))
                        await interaction.response.edit_message(view=view)
                    else:
                        print('Cancelled...')

    await interaction.response.send_message(f"Entry not found.", ephemeral=True)


# Define a simple View that gives us a confirmation menu
class Pages(discord.ui.View):
    def __init__(self, page_count: int):
        super().__init__()
        self.index = 0
        self.page_count = page_count
    
    @discord.ui.button(label='Previous page', style=discord.ButtonStyle.primary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button, ):
        await interaction.response.send_message('Confirming', ephemeral=True)
        self.index = max(0, self.index - 1)
        print(self.index)
        await self.update_buttons()

    
    @discord.ui.button(label='Next page', style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Cancelling', ephemeral=True)
        self.index = min(self.page_count, self.index + 1)
        print(self.index)
        print("page count" + str(self.page_count))
        await self.update_buttons()
    
    async def update_buttons(self):
        print("update buttons")
        self.children[0].disabled = (self.index == 0)
        self.children[1].disabled = (self.index == self.page_count)

            
'''


bot.run(os.environ.get("TOKEN"))
