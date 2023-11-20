import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
import os 
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


def fetch_movie_data(movie_title, year):
    base_url = "http://www.omdbapi.com/"
    api_key = os.environ.get("OMDB_API_KEY")

    params = {
        'apikey': api_key,
        't': movie_title,  # You can use 't' for movie title or 'i' for IMDb ID
        'y': year
    }

    try:
        request_url = f"{base_url}?{'&'.join([f'{key}={value}' for key, value in params.items()])}"

        #print("Request URL:", request_url)  # Print the request URL

        response = requests.get(request_url)
        data = response.json()

        if data['Response'] == 'True':
            # Movie data fetched successfully
            return data
        else:
            # Handle API response errors
            print("Error: ", data['Error'])
            return None

    except requests.RequestException as e:
        # Handle connection errors
        print("Request Exception:", e)
        return None


# Fetches ISBN of the oldest book with the given title
def fetch_book_data(query):
    search_url = f'https://www.goodreads.com/search?q={query}&qid='

    # Start a browser session
    driver = webdriver.Firefox()

    driver.get(search_url)

    table_body = driver.find_element(By.TAG_NAME, 'tbody')

    # Get the first row of the table
    first_row = table_body.find_element(By.TAG_NAME, 'tr')

    # Get the second column of the row
    second_column = first_row.find_elements(By.TAG_NAME, 'td')[1]

    # Get the anchor tag inside the second column
    anchor_tag = second_column.find_element(By.TAG_NAME, 'a')

    # Get the href attribute of the anchor tag
    href = anchor_tag.get_attribute('href')

    book_url = href

    print("Book URL:", book_url)

fetch_book_data('The Alchemist')