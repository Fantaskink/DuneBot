import requests
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
    key = fetch_book_key(query)

    if key is None:
        return None
    
    base_url = f"https://openlibrary.org/{key}.json"

    response = requests.get(base_url)

    if response.status_code == 200:
        data = response.json()
        return data


def fetch_book_key(query):
    
    # Fill whitespace in query with '+'
    query = query.replace(" ", "+")

    base_url = "https://openlibrary.org/search.json?"
    params = {"title": query, "limit": 1}

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data['numFound'] > 0:
            return data['docs'][0]['key']
        else:
            return None


def fetch_author_from_key(key):
    base_url = f"https://openlibrary.org/{key}.json"

    response = requests.get(base_url)

    if response.status_code == 200:
        data = response.json()
        return data['name']
    else:
        return None