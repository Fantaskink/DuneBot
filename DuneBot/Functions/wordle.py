import discord
from discord import app_commands
from discord.ext import commands
import csv
import os
import random
from typing import Union, List
from config import get_base_path, ENVIRONMENT, PRODUCTION_BASE_PATH, DEVELOPMENT_BASE_PATH


DUNE_SOLUTIONS_PATH = 'wordle/dune_solutions.csv'
VALID_GUESSES_PATH = 'wordle/valid_guesses.csv'
VALID_SOLUTIONS_PATH = 'wordle/valid_solutions.csv'
PLAYER_STATS_PATH = 'wordle/player_stats.csv'


def get_random_solution(dune_mode: bool) -> Union[str, None]:
    file_path = get_base_path() + (DUNE_SOLUTIONS_PATH if dune_mode else VALID_SOLUTIONS_PATH)

    try:
        with open(file_path, 'r') as f:
            solutions = f.read().splitlines()
            return random.choice(solutions)
    except FileNotFoundError as e:
        print(f"Error opening file: {e}")
        return None


class wordle_game:
    def __init__(self, user_id, dune_mode: bool):
        self.user_id = user_id
        self.dune_mode = dune_mode
        self.word = get_random_solution(dune_mode)
        self.guesses_left = 6
        self.discarded_letters = set()
    
    def get_user_id(self):
        return self.user_id
    
    def get_word(self):
        return self.word

    def get_word_length(self):
        return len(self.word)
    
    def set_word(self, word):
        self.word = word

    def get_guesses_left(self):
        return self.guesses_left
    
    def subtract_guess(self):
        self.guesses_left -= 1

    def is_dune_mode(self):
        return self.dune_mode
    
    def update_discarded_letters(self, discarded_letters):
        self.discarded_letters.update(discarded_letters)

    def get_discarded_letters(self):
        return self.discarded_letters
    

class WordleCog(commands.GroupCog, name="wordle"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.wordle_games: List[wordle_game] = []
    

    def get_wordle_game(self, user_id):
        for wordle_game in self.wordle_games:
            if wordle_game.get_user_id() == user_id:
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
            length = new_game.get_word_length()
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
        
        if len(guess) != game.get_word_length():
            length = game.get_word_length()
            await interaction.followup.send(f"Guess must be {length} letters long.")
            return

        # If guess contains non-alphabetical characters
        if not guess.isalpha():
            await interaction.followup.send("Guess must contain only letters.")
            return
        
        if not game.is_dune_mode():
            valid_guesses = get_valid_guesses()
            solutions = get_all_solutions()
            if guess not in valid_guesses and guess not in solutions:
                await interaction.followup.send("Not a word.")
                return
        
        result_string = check_guess(guess, game)

        await interaction.channel.send(interaction.user.display_name + " guessed: " + guess.upper())

        await interaction.channel.send(result_string)

        if guess == game.get_word():
            await interaction.followup.send("You win!")
            self.end_wordle_game(interaction.user.id)
            player_win_game(str(interaction.user.id))
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
            self.end_wordle_game(interaction.user.id)
            await interaction.followup.send("Play again with /wordle.")
            player_lose_game(str(interaction.user.id))
            return
        
        await interaction.followup.send("Guess again with /guess")
        return


    @app_commands.command(name="wordle_player_stats", description="Get the stats of a player.")
    @app_commands.describe(player="The player you want to get stats for.")
    @app_commands.guild_only()
    async def wordle_player_stats(self, interaction: discord.Interaction, player: discord.User):
        if player_in_stats(str(player.id)):
            wins = get_wins(str(player.id))
            losses = get_losses(str(player.id))
            win_rate = get_win_percentage(str(player.id))
            await interaction.response.send_message(f"{player.display_name} has {wins} wins and {losses} losses.\n Win rate: {win_rate}%")
        else:
            await interaction.response.send_message(f"{player.display_name} has not played any wordle games")


async def setup(bot: commands.Bot): 
    await bot.add_cog(WordleCog(bot))


def get_valid_guesses():
    file_path = get_base_path() + VALID_GUESSES_PATH
    with open(file_path, 'r') as f:
        valid_guesses = f.read().splitlines()
        return valid_guesses


def get_all_solutions():
    file_path = get_base_path() + VALID_SOLUTIONS_PATH
    with open(file_path, 'r') as f:
        valid_solutions = f.read().splitlines()
        return valid_solutions


def check_guess(guess: str, game: wordle_game):
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


def player_in_stats(user_id:str ):
    file_path = get_base_path() + PLAYER_STATS_PATH

    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        print("File is empty or doesn't exist")
        return False
    
    with open(file_path, 'r') as stats_file:
        csv_reader = csv.reader(stats_file)

        for row in csv_reader:
            if row[0] == user_id:
                return True

        return False
    

def player_win_game(user_id: str):
    # If player is not in stats.csv, add them
    if not player_in_stats(str(user_id)):
        add_player_to_stats(user_id)
    
    # Update stats.csv and add 1 to second column
    with open(get_base_path() + PLAYER_STATS_PATH, 'r') as stats_file:
        csv_reader = csv.reader(stats_file)
        lines = list(csv_reader)
        for i in range(len(lines)):
            if lines[i][0] == user_id:
                lines[i][1] = int(lines[i][1]) + 1
    
    # Write to stats.csv
    with open(get_base_path() + PLAYER_STATS_PATH, 'w') as stats_file:
        csv_writer = csv.writer(stats_file)
        csv_writer.writerows(lines)


def player_lose_game(user_id: str):
    # If player is not in stats.csv, add them
    if not player_in_stats(user_id):
        add_player_to_stats(user_id)
    
    # Update stats.csv and add 1 to third column
    with open(get_base_path() + PLAYER_STATS_PATH, 'r') as stats_file:
        csv_reader = csv.reader(stats_file)
        lines = list(csv_reader)
        for i in range(len(lines)):
            if lines[i][0] == user_id:
                lines[i][2] = int(lines[i][2]) + 1
    
    # Write to stats.csv
    with open(get_base_path() + PLAYER_STATS_PATH, 'w') as stats_file:
        csv_writer = csv.writer(stats_file)
        csv_writer.writerows(lines)


def add_player_to_stats(user_id: str):
    with open(get_base_path() + PLAYER_STATS_PATH, 'a') as stats_file:
        csv_writer = csv.writer(stats_file)
        csv_writer.writerow([user_id, 0, 0])


def get_wins(user_id: str):
    with open(get_base_path() + PLAYER_STATS_PATH, 'r') as stats_file:
        csv_reader = csv.reader(stats_file)

        for row in csv_reader:
            if row[0] == user_id:
                return row[1]


def get_losses(user_id: str):
    with open(get_base_path() + PLAYER_STATS_PATH, 'r') as stats_file:
        csv_reader = csv.reader(stats_file)

        for row in csv_reader:
            if row[0] == user_id:
                return row[2]


def get_win_percentage(user_id: str):
    with open(get_base_path() + PLAYER_STATS_PATH, 'r') as stats_file:
        csv_reader = csv.reader(stats_file)

        for row in csv_reader:
            if row[0] == user_id:
                if int(row[1]) + int(row[2]) == 0:
                    return 0
                else:
                    return round(int(row[1]) / (int(row[1]) + int(row[2])) * 100, 2)