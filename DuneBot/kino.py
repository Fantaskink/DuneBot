import requests
import os 
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


def get_movie_data(movie_title, year):
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

# Replace 'Your Movie Title' with the movie you want to search for
#movie_title = 'Barbie'
#year = '2023'
#movie_data = get_movie_data(movie_title, year)

#print(movie_data)



#if movie_data:
    # Display the fetched movie data
    #print("Title:", movie_data['Title'])
    #print("Year:", movie_data['Year'])
    #print("IMDb Rating:", movie_data['imdbRating'])
    #print("Rotten Tomatoes Score:", movie_data['Value'])
    #print("Plot:", movie_data['Plot'])
    # Add more details as needed
#else:
    #print("No movie data found.")
