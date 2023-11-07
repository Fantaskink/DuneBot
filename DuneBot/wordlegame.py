import os
import random


def get_random_solution(dune_mode):
    environment = os.environ.get("ENVIRONMENT")
    base_path = ''

    if environment == "production":
        base_path = '/home/ubuntu/DuneBot/DuneBot/'
    elif environment == "development":
        base_path = 'DuneBot/'

    if dune_mode:
        with open(base_path + 'wordle/dune_solutions.csv', 'r') as f:
            dune_solutions = f.read().splitlines()
            return random.choice(dune_solutions)
    else:
        print(base_path + 'wordle/valid_solutions.csv')
        with open(base_path + 'wordle/valid_solutions.csv', 'r') as f:
            valid_solutions = f.read().splitlines()
            return random.choice(valid_solutions)
    

class wordle_game:
    def __init__(self, user_id, dune_mode):
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
    