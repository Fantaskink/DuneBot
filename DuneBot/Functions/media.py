import discord
from discord import app_commands
from discord.ext import commands
import requests
import urllib.parse
from bs4 import BeautifulSoup
from colorthief import ColorThief
from io import BytesIO
from config import OMDB_API_KEY


class MediaCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="kino", description="Get media links")
    @app_commands.describe(movie_title="Type in the name of the movie you wish to look up.", year="Type in the year the movie was released.")
    async def kino(self, interaction: discord.Interaction, movie_title: str, year: str) -> None:
        await interaction.response.defer()

        movie_data = fetch_movie_data(movie_title, year)

        if movie_data is None:
            await interaction.followup.send("Movie not found")

        if movie_data['Poster'] == 'N/A':
            color_hex = discord.Colour.blue()
        else:
            color_hex = get_primary_hex_color(movie_data['Poster'])

        title = movie_data['Title'] + " (" + movie_data['Year'] + ")"

        movie_link = f"https://www.imdb.com/title/{movie_data['imdbID']}"

        discord_embed = discord.Embed(title=title, url=movie_link, color=color_hex)
        
        if movie_data['Poster'] != 'N/A':
            thumbnail_url = movie_data['Poster']
            discord_embed.set_thumbnail(url=thumbnail_url)

        discord_embed.add_field(name='Director', value=movie_data['Director'], inline=False)
        discord_embed.add_field(name='Genre', value=movie_data['Genre'], inline=True)
        discord_embed.add_field(name='Runtime', value=movie_data['Runtime'], inline=True)
        discord_embed.add_field(name='Description', value=movie_data['Plot'], inline=False)
        discord_embed.add_field(name='IMDb Rating', value=movie_data['imdbRating'], inline=True)

        rotten_tomatoes_score = None
        for rating in movie_data['Ratings']:
            if rating['Source'] == 'Rotten Tomatoes':
                rotten_tomatoes_score = rating['Value']


        discord_embed.add_field(name='Rotten Tomatoes Score', value=rotten_tomatoes_score, inline=True)
        discord_embed.add_field(name='Metacritic Score', value=movie_data['Metascore'], inline=True)
        discord_embed.add_field(name='Box Office', value=movie_data['BoxOffice'], inline=False)

        await interaction.followup.send(embed=discord_embed)


    @app_commands.command(name="book", description="Get book information")
    @app_commands.describe(book_title="Type in the name of the book you wish to look up.")
    async def book(self, interaction: discord.Interaction, book_title: str):
        await interaction.response.defer()

        data = fetch_book_data(book_title)

        if data is None:
            await interaction.followup.send("Book not found")
            return

        title = data['title']
        author = data['author']
        rating = data['rating'] + "/5"
        thumbnail_url = data['thumbnail_url']
        page_count = data['page_count'][0]
        publish_date = data['publish_date'][0]
        book_link = data['book_link']


        if 'description' not in data:
            long_description = "No description available"
        else:
            long_description = data['description']
            short_description = (long_description[:500] + '...') if len(long_description) > 75 else long_description
        
        color_hex = get_primary_hex_color(thumbnail_url)

        discord_embed = discord.Embed(title=title, url=book_link, color=color_hex)

        discord_embed.set_thumbnail(url=thumbnail_url)

        discord_embed.add_field(name='Authors', value=author, inline=True)
        discord_embed.add_field(name='Published', value=publish_date, inline=True)
        discord_embed.add_field(name='Description', value=short_description, inline=False)
        discord_embed.add_field(name='Page Count', value=page_count, inline=True)
        discord_embed.add_field(name='Rating', value=rating, inline=True)

        await interaction.followup.send(embed=discord_embed)

def fetch_movie_data(movie_title, year):
    base_url = "http://www.omdbapi.com/"

    params = {
        'apikey': OMDB_API_KEY,
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


def get_primary_hex_color(image_url):
    response = requests.get(image_url)

    color_thief = ColorThief(BytesIO(response.content))

    dominant_color = color_thief.get_color(quality=1)

    # Convert the RGB values to hex
    primary_hex = '#{:02x}{:02x}{:02x}'.format(*dominant_color)
    
    return int(primary_hex[1:], 16)


async def setup(bot: commands.Bot) -> None: 
    await bot.add_cog(MediaCog(bot))