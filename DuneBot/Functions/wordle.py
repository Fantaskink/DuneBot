import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
from typing import Union, List
from config import get_base_path


DUNE_SOLUTIONS_PATH = 'wordle/dune_solutions.csv'
VALID_GUESSES_PATH = 'wordle/valid_guesses.csv'
VALID_SOLUTIONS_PATH = 'wordle/valid_solutions.csv'
PLAYER_STATS_PATH = 'wordle/player_stats.csv'


def get_random_solution(dune_mode: bool) -> Union[str, None]:
    conn = sqlite3.connect(get_base_path() + '/db/wordle.db')
    c = conn.cursor()

    if dune_mode:
        c.execute("SELECT word FROM dune_solutions ORDER BY RANDOM() LIMIT 1")
    else:
        c.execute("SELECT word FROM standard_solutions ORDER BY RANDOM() LIMIT 1")
    
    result = c.fetchone()
    conn.close()

    if result is None:
        return None
    else:
        return result[0]


class wordle_game:
    def __init__(self, user_id, dune_mode: bool) -> None:
        self.user_id = user_id
        self.dune_mode = dune_mode
        self.word = get_random_solution(dune_mode)
        self.guesses_left = 6
        self.discarded_letters = set()
    

class WordleCog(commands.GroupCog, name="wordle"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.wordle_games: List[wordle_game] = []
    

    def get_wordle_game(self, user_id) -> Union[wordle_game, None]:
        for wordle_game in self.wordle_games:
            if wordle_game.user_id == user_id:
                return wordle_game
        return None


    def end_wordle_game(self, user_id: discord.User.id) -> None:
        wordle_game = self.get_wordle_game(user_id)
        self.wordle_games.remove(wordle_game)


    @app_commands.command(name="begin_game", description="Start a new Wordle game")
    @app_commands.describe(dune_mode="Choose yes to play wordle with terms and names from Dune. Choose no to play with standard words.")
    @app_commands.guild_only()
    async def wordle(self, interaction: discord.Interaction, dune_mode: bool = False) -> None:
        """ /wordle begin_game """
        game_in_progress = self.get_wordle_game(interaction.user.id)

        if game_in_progress is None:
            new_game = wordle_game(interaction.user.id, dune_mode)
            self.wordle_games.append(new_game)
            length = len(new_game.word)
            await interaction.response.send_message(f"Wordle game started. \n Guess a {length} letter word with /guess", ephemeral=True)
        else:
            await interaction.response.send_message("You already have a wordle game in progress", ephemeral=True)
    
    @app_commands.command(name="guess", description="Type in the word you wish to guess.")
    @app_commands.guild_only()
    async def guess(self, interaction: discord.Interaction, guess: str):
        await interaction.response.defer(ephemeral=True)

        guess = guess.lower().strip()
        game = self.get_wordle_game(interaction.user.id)

        if game is None:
            await interaction.followup.send("You do not have a wordle game in progress.")
            return
        
        if len(guess) != len(game.word):
            length = len(game.word)
            await interaction.followup.send(f"Guess must be {length} letters long.")
            return

        # If guess contains non-alphabetical characters
        if not guess.isalpha():
            await interaction.followup.send("Guess must contain only letters.")
            return
        
        if not game.dune_mode:
            valid_guesses = get_valid_guesses()
            solutions = get_all_solutions()
            if guess not in valid_guesses and guess not in solutions:
                await interaction.followup.send("Not a word.")
                return
        
        result_string = check_guess(guess, game)

        await interaction.channel.send(interaction.user.display_name + " guessed: " + guess.upper())

        await interaction.channel.send(result_string)

        if guess == game.word:
            await interaction.followup.send("You win!")
            self.end_wordle_game(interaction.user.id)
            player_win_game(str(interaction.user.id))
            return
        
        discarded_letters = game.discarded_letters
        discarded_letters_list = list(discarded_letters)  # Convert the set to a list
        discarded_letters_string = ""

        last_item = discarded_letters_list[-1]
        for element in discarded_letters_list:
            if element == last_item:
                discarded_letters_string += element
            else:
                discarded_letters_string += element + ", "

        await interaction.channel.send("Discarded letters: " +  discarded_letters_string)
        
        game.guesses_left -= 1

        await interaction.channel.send("Guesses left: " + str(game.guesses_left))

        if game.guesses_left == 0:
            await interaction.channel.send("You lose!")
            await interaction.channel.send("The word was: " + game.word.upper())
            self.end_wordle_game(interaction.user.id)
            await interaction.followup.send("Play again with /wordle.")
            player_lose_game(str(interaction.user.id))
            return
        
        await interaction.followup.send("Guess again with /guess")
        return


    @app_commands.command(name="wordle_player_stats", description="Get the stats of a player.")
    @app_commands.describe(player="The player you want to get stats for.")
    @app_commands.guild_only()
    async def wordle_player_stats(self, interaction: discord.Interaction, player: discord.User) -> None:
        if player_in_stats(str(player.id)):
            wins = get_wins(str(player.id))
            losses = get_losses(str(player.id))
            win_rate = get_win_percentage(str(player.id))
            await interaction.response.send_message(f"{player.display_name} has {wins} wins and {losses} losses.\n Win rate: {win_rate}%")
        else:
            await interaction.response.send_message(f"{player.display_name} has not played any wordle games")
    

    @app_commands.command(name='setup_database', description="Setup the wordle database.")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.default_permissions(ban_members=True)
    async def setup_database(self, interaction: discord.Interaction) -> None:
        setup_db()
        await interaction.response.send_message("Database setup complete.")



async def setup(bot: commands.Bot) -> None: 
    await bot.add_cog(WordleCog(bot))


def get_valid_guesses():
    conn = sqlite3.connect(get_base_path() + '/db/wordle.db')
    c = conn.cursor()

    c.execute("SELECT word FROM valid_guesses")
    valid_guesses = c.fetchall()

    conn.close()

    return valid_guesses



def get_all_solutions():
    # Get standard solutions
    conn = sqlite3.connect(get_base_path() + '/db/wordle.db')

    c = conn.cursor()

    c.execute("SELECT word FROM standard_solutions")

    standard_solutions = c.fetchall()

    # Return solutions

    return standard_solutions



def check_guess(guess: str, game: wordle_game):
    solution = game.word
    solution_length = len(game.word)
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
                game.discarded_letters.add(guess[i])

    output_string = "".join(output)

    return output_string


def player_in_stats(user_id) -> bool:
    conn = sqlite3.connect(get_base_path() + '/db/wordle.db')
    c = conn.cursor()

    c.execute("SELECT user_id FROM player_stats WHERE user_id = ?", (user_id,))

    result = c.fetchone()
    conn.close()

    if result is None:
        return False
    else:
        return True
    

def player_win_game(user_id: str):
    # If player is not in stats.csv, add them
    if not player_in_stats(str(user_id)):
        add_player_to_stats(user_id)
    
    # Update player_stats table and add 1 to games_won column
    conn = sqlite3.connect(get_base_path() + '/db/wordle.db')
    c = conn.cursor()

    c.execute("SELECT games_won FROM player_stats WHERE user_id = ?", (user_id,))

    result = c.fetchone()

    if result is None:
        return
    else:
        games_won = result[0]
        games_won += 1
        c.execute("UPDATE player_stats SET games_won = ? WHERE user_id = ?", (games_won, user_id))
        conn.commit()
        conn.close()


def player_lose_game(user_id: str):
    # If player is not in player_stats table, add them
    if not player_in_stats(str(user_id)):
        add_player_to_stats(user_id)

    # Update player_stats table and add 1 to games_lost column
    conn = sqlite3.connect(get_base_path() + '/db/wordle.db')
    c = conn.cursor()

    c.execute("SELECT games_lost FROM player_stats WHERE user_id = ?", (user_id,))
    result = c.fetchone()

    if result is None:
        return
    else:
        games_lost = result[0]
        games_lost += 1
        c.execute("UPDATE player_stats SET games_lost = ? WHERE user_id = ?", (games_lost, user_id))
        conn.commit()
        conn.close()


def add_player_to_stats(user_id: str):
    conn = sqlite3.connect(get_base_path() + '/db/wordle.db')

    c = conn.cursor()

    c.execute("INSERT INTO player_stats (user_id, games_played, games_won, games_lost, total_guesses, correct_guesses, incorrect_guesses) VALUES (?, ?, ?, ?, ?, ?, ?)", (user_id, 0, 0, 0, 0, 0, 0))


def get_wins(user_id: str):
    conn = sqlite3.connect(get_base_path() + '/db/wordle.db')

    c = conn.cursor()

    c.execute("SELECT games_won FROM player_stats WHERE user_id = ?", (user_id,))

    result = c.fetchone()
    conn.close()

    if result is None:
        return None
    else:
        return result[0]


def get_losses(user_id: str):
    conn = sqlite3.connect(get_base_path() + '/db/wordle.db')

    c = conn.cursor()

    c.execute("SELECT games_lost FROM player_stats WHERE user_id = ?", (user_id,))

    result = c.fetchone()
    conn.close()

    if result is None:
        return None
    else:
        return result[0]


def get_win_percentage(user_id: str):
    conn = sqlite3.connect(get_base_path() + '/db/wordle.db')

    c = conn.cursor()

    c.execute("SELECT games_won, games_lost FROM player_stats WHERE user_id = ?", (user_id,))

    result = c.fetchone()
    conn.close()

    if result is None:
        return None
    else:
        wins = result[0]
        losses = result[1]
        total_games = wins + losses

        if total_games == 0:
            return 0
        else:
            win_rate = (wins / total_games) * 100
            return round(win_rate, 2)


def setup_db() -> None:
    conn = sqlite3.connect(get_base_path() + '/db/wordle.db')

    c = conn.cursor()

    # Drop all tables but sql_sequence
    result = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_sequence';")
    tables = result.fetchall()

    for table in tables:
        c.execute(f"DROP TABLE {table[0]}")

    # Create solutions table
    c.execute(""" CREATE TABLE standard_solutions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT
            )""")

    # Create a dune solutions table
    c.execute(""" CREATE TABLE dune_solutions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT
            )""")

    c.execute(""" CREATE TABLE valid_guesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT
            )""")

    # Create player stats table
    c.execute(""" CREATE TABLE player_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                games_played INTEGER,
                games_won INTEGER,
                games_lost INTEGER,
                total_guesses INTEGER,
                correct_guesses INTEGER,
                incorrect_guesses INTEGER
                )"""
    )

    # Add standard solutions to the standard solutions table
    with open(VALID_SOLUTIONS_PATH, 'r') as file:
        for line in file:
            c.execute("INSERT INTO standard_solutions (word) VALUES (?)", (line.strip(),))

    # Add dune solutions to the dune solutions table
    with open(DUNE_SOLUTIONS_PATH, 'r') as file:
        for line in file:
            c.execute("INSERT INTO dune_solutions (word) VALUES (?)", (line.strip(),))

    # Add valid guesses to the valid guesses table
    with open(VALID_GUESSES_PATH, 'r') as file:
        for line in file:
            c.execute("INSERT INTO valid_guesses (word) VALUES (?)", (line.strip(),))

    # Add player stats to the player stats table
    with open(PLAYER_STATS_PATH, 'r') as file:
        for line in file:
            user_id, games_won, games_lost = line.strip().split(',')
            user_id = int(user_id)
            games_won = int(games_won)
            games_lost = int(games_lost)
            c.execute("INSERT INTO player_stats (user_id, games_played, games_won, games_lost, total_guesses, correct_guesses, incorrect_guesses) VALUES (?, ?, ?, ?, ?, ?, ?)", (user_id, 0, games_won, games_lost, 0, 0, 0))


    conn.commit()
    conn.close()