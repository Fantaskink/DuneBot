import requests
import os 
from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub
import urllib.parse
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

environment = os.environ.get("ENVIRONMENT")
base_path = ""

if environment == "production":
    base_path = '/home/ubuntu/DuneBot/DuneBot/'
elif environment == "development":
    base_path = 'DuneBot/'


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

    except Exception as e:
        return None


# Fetches ISBN of the oldest book with the given title
def fetch_book_data(query):
    try:
        book_link = search_title_on_goodreads(query)
        
        response = requests.get(book_link)

        soup = BeautifulSoup(response.content, 'html.parser')

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
    
    except Exception as e:
        print("Exception:", e)
        return None


def search_title_on_goodreads(query):
    query = urllib.parse.quote_plus(query)
    search_url = f'https://www.goodreads.com/search?utf8=✓&q={query}&search_type=books&search%5Bfield%5D=on'
    
    try:
        response = requests.get(search_url)

        soup = BeautifulSoup(response.content, 'html.parser')

        table = soup.find('table', class_='tableList')

        anchor = table.find('a')

        href = anchor['href']
        
        return 'https://www.goodreads.com' + href
    except Exception as e:
        print("Exception:", e)
        return None


def search_in_epub_with_element(search_term, index, element):
    book_path = f"{base_path}book/dune_{index}.epub"

    book = epub.read_epub(book_path)

    results = []

    for item_id, item in enumerate(book.get_items_of_type(ebooklib.ITEM_DOCUMENT)):
        soup = BeautifulSoup(item.get_body_content(), 'html.parser')

        text = [para.get_text() for para in soup.find_all(element)]

        for line in text:
            if search_term.lower() in line.lower():
                if len(line) > 1024: # Truncate the line if it's too long for a discord message
                    line = line[:1010] + "..."
                results.append({"results":line, "book_number":index})
    
    if results:
        return results
    else:
        return None

#print(search_in_epub_with_element("beefswelling", 3, "p"))