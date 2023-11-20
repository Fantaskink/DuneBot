import requests
import os 
from bs4 import BeautifulSoup
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
    book_link = search_title_on_goodreads(query)

    if book_link is None:
        return None
    
    response = requests.get(book_link)

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the element with class "Text Text__title1"
    title_header = soup.find(class_="Text Text__title1")

    author_span = soup.find(class_="ContributorLink__name")

    rating_div = soup.find(class_="RatingStatistics__rating")

    thumbnail_img = soup.find(class_="ResponsiveImage")['src']

    description_span = soup.find(class_="Formatted")

    details_div = soup.find(class_="FeaturedDetails")

    p_elements = details_div.find_all('p')

    data = {}

    data['title'] = title_header.text
    data['author'] = author_span.text
    data['rating'] = rating_div.text
    data['thumbnail_url'] = thumbnail_img
    data['description'] = description_span.text
    data['page_count'] = [p_elements[0].get_text()]
    data['publish_date'] = [p_elements[1].get_text()]
    data['book_link'] = book_link

    return data

    

def search_title_on_goodreads(query):
    # Replace whitespace in query with +
    query = query.replace(' ', '+')
    search_url = f'https://www.goodreads.com/search?q={query}&qid='
    try:
        response = requests.get(search_url)

        soup = BeautifulSoup(response.content, 'html.parser')

        table = soup.find('table', class_='tableList')

        anchor = table.find('a')

        href = anchor['href']
        
        return 'https://www.goodreads.com' + href
    except requests.RequestException as e:
        print("Request Exception:", e)
        return None