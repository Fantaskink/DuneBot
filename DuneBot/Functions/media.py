import discord
from discord import app_commands
from discord.ext import commands


class MediaCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="kino", description="Get media links")
    @app_commands.describe(movie_title="Type in the name of the movie you wish to look up.", year="Type in the year the movie was released.")
    async def kino(self, interaction: discord.Interaction, movie_title: str, year: str) -> None:
        await interaction.response.defer()
        from media_fetcher import fetch_movie_data
        from primarycolor import get_primary_hex_color

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
        from media_fetcher import fetch_book_data
        from primarycolor import get_primary_hex_color

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

async def setup(bot: commands.Bot) -> None: 
    await bot.add_cog(MediaCog(bot))