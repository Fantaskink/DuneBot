import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from datetime import date, datetime, time
import csv
import os
import re
from dotenv import load_dotenv, find_dotenv
from wordlegame import wordle_game

load_dotenv(find_dotenv())

intents = discord.Intents.default()
intents.message_content = True

global bot
bot = commands.Bot(command_prefix='!', intents=intents)

environment = os.environ.get("ENVIRONMENT")
print("Environment:", environment)

wordle_games = []

base_path = ""

if environment == "production":
    base_path = '/home/ubuntu/DuneBot/DuneBot/'
elif environment == "development":
    base_path = 'DuneBot/'

@bot.event
async def on_ready():
    update_presence_task.start()

    print(f'{bot.user} is now running.')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

@bot.event
async def on_message(message: discord.Message):
    await check_spoiler(message)
    

async def check_spoiler(message):
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
                    await modlog_channel.send(f"Spoiler reminder sent in {message.channel.mention}, triggered by keyword: {keyword}. ```{message.content}``` Jump to message: {message.jump_url}")
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


def is_marked_spoiler(text, keyword):
    pattern = rf'.*\|\|.*{re.escape(keyword)}.*\|\|.*'
    return re.match(pattern, text)


async def update_presence():
    days_until_string = await get_days_until_string("2024-03-15", "00:00")

    #days_until_string = "ITS FUCKING DELAYED"

    activity = discord.CustomActivity(name=days_until_string)
    await bot.change_presence(activity=activity)
    

@tasks.loop(hours=24)
async def update_presence_task():
    await update_presence()

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

    # Prevent command from being run twice when testing bot
    if environment == "production" and interaction.guild_id != 701674250591010837:
        print("wrong server")
        return
    
    if environment == "development" and interaction.guild_id != 1064479981012533300:
        print("wrong server")
        return

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
        player_win_game(interaction.user.id)
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
        player_lose_game(interaction.user.id)
        return
    
    await interaction.followup.send("Guess again with /guess")
    return


async def check_guess(guess, game: wordle_game):
    solution = game.get_word()
    solution_length = game.get_word_length()
    output = ["_" for _ in range(solution_length)]
    letters = []
    
    for i in range(0, solution_length):
        letters.append(solution[i])

    for i in range(0, solution_length):
        if guess[i] in solution and guess[i] in letters and guess[i] != solution[i]:
            output[i] = "🟨"
            letters.remove(guess[i])
        elif guess[i] == solution[i]:
            output[i] = "🟩"
            letters.remove(guess[i])
        else:
            output[i] = "⬜"
            if guess[i] not in solution:
                game.update_discarded_letters(guess[i])

    output_string = ""
    for letter in output:
        output_string += letter

    return output_string

async def end_wordle_game(user_id: discord.User.id):
    wordle_game = await get_wordle_game(user_id)
    await remove_wordle_game(wordle_game)
    

def player_in_stats(user_id):
    with open(base_path + 'wordle/player_stats.csv', 'r') as stats_file:
        csv_reader = csv.reader(stats_file)

        for row in csv_reader:
            if row[0] == user_id:
                return True

        return False
    

def player_win_game(user_id):
    # If player is not in stats.csv, add them
    if not player_in_stats(user_id):
        add_player_to_stats(user_id)
    
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


def player_lose_game(user_id):
    # If player is not in stats.csv, add them
    if not player_in_stats(user_id):
        add_player_to_stats(user_id)
    
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


def add_player_to_stats(user_id):
    with open(base_path + 'wordle/player_stats.csv', 'a') as stats_file:
        csv_writer = csv.writer(stats_file)
        csv_writer.writerow([user_id, 0, 0])


def get_wins(user_id):
    with open(base_path + 'wordle/player_stats.csv', 'r') as stats_file:
        csv_reader = csv.reader(stats_file)

        for row in csv_reader:
            if row[0] == user_id:
                return row[1]


def get_losses(user_id):
    with open(base_path + 'wordle/player_stats.csv', 'r') as stats_file:
        csv_reader = csv.reader(stats_file)

        for row in csv_reader:
            if row[0] == user_id:
                return row[2]


@bot.tree.command(name="wordle_player_stats")
@app_commands.describe(player="Type in the name of the player whose stats you wish to see.")
async def wordle_player_stats(interaction: discord.Interaction, player: discord.User):
    if player_in_stats(player.id):
        wins = get_wins(player.id)
        losses = get_losses(player.id)
        await interaction.response.send_message(f"{player.display_name} has {wins} wins and {losses} losses")
    else:
        await interaction.response.send_message(f"{player.display_name} has not played any wordle games")





'''

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

            
'''


bot.run(os.environ.get("TOKEN"))
