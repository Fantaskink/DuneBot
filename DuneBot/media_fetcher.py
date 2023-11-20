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

        print("Request URL:", request_url)  # Print the request URL

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

def fetch_book_data(query):
    base_url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": query, "maxResults": 1}

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()

        return data

        # Extract and display book information
        for item in data.get("items", []):
            volume_info = item.get("volumeInfo", {})
            title = volume_info.get("title")
            authors = volume_info.get("authors", "Unknown")
            print(f"Title: {title}")
            print(f"Authors: {', '.join(authors)}")
            print("------------")
    else:
        return None