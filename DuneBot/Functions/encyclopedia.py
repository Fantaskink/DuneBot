import discord
from discord import app_commands
from discord.ext import commands
import re

def get_title_from_index(index):
    match (index):
        case (1):
            return "Dune"
        case (2):
            return "Dune Messiah"
        case (3):
            return "Children of Dune"
        case (4):
            return "God Emperor of Dune"
        case (5):
            return "Heretics of Dune"
        case (6):
            return "Chapterhouse Dune"
        case (_):
            return "Unknown"


class SearchResultView(discord.ui.View):
    def __init__(self, data, search_term):
        super().__init__()
        self.data = data
        self.search_term = search_term
        self.current_page = 1
        self.timeout = 600
    
    async def send(self, interaction: discord.Interaction):
        self.message = await interaction.followup.send(view=self)
        await self.update_message(self.data[self.current_page - 1])

    def create_embed(self, data: dict):
        embed = discord.Embed(title=f"Search Result Page {self.current_page} of {len(self.data)}", color=discord.Colour.dark_gold())
        title = get_title_from_index(data["book_number"])
        embed.add_field(name="Found in", value=title, inline=False)

        result = data["results"]

        result = re.sub(f'({self.search_term})', r'***\1***', result, flags=re.IGNORECASE)

        if data["book_number"] == 1:
            embed.add_field(name="Excerpt", value=result, inline=False)
        else:
            embed.add_field(name="Excerpt", value=f"||{result}||", inline=False)
        
        return embed
    
    def update_buttons(self):
        if self.current_page == 1:
            self.first_page_button.disabled = True
            self.prev_button.disabled = True
            self.first_page_button.style = discord.ButtonStyle.gray
            self.prev_button.style = discord.ButtonStyle.gray
        else:
            self.first_page_button.disabled = False
            self.prev_button.disabled = False
            self.first_page_button.style = discord.ButtonStyle.green
            self.prev_button.style = discord.ButtonStyle.primary

        if self.current_page == len(self.data):
            self.next_button.disabled = True
            self.last_page_button.disabled = True
            self.last_page_button.style = discord.ButtonStyle.gray
            self.next_button.style = discord.ButtonStyle.gray
        else:
            self.next_button.disabled = False
            self.last_page_button.disabled = False
            self.last_page_button.style = discord.ButtonStyle.green
            self.next_button.style = discord.ButtonStyle.primary
    
    async def on_timeout(self):
        self.first_page_button.disabled = True
        self.prev_button.disabled = True
        self.next_button.disabled = True
        self.last_page_button.disabled = True
        self.clear_items()
        self.stop()

        await self.update_message(self.data[self.current_page - 1])


    @discord.ui.button(label="|<", style=discord.ButtonStyle.primary)
    async def first_page_button(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.defer()
        self.current_page = 1
        await self.update_message(self.data[self.current_page - 1])

    @discord.ui.button(label="<", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.defer()
        self.current_page -= 1
        await self.update_message(self.data[self.current_page - 1])

    @discord.ui.button(label=">", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.defer()
        self.current_page += 1
        await self.update_message(self.data[self.current_page - 1])

    @discord.ui.button(label=">|", style=discord.ButtonStyle.primary)
    async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.button):
        await interaction.response.defer()
        self.current_page = len(self.data)
        await self.update_message(self.data[self.current_page - 1])

    
    async def update_message(self, data):
        self.update_buttons()
        await self.message.edit(embed=self.create_embed(data), view=self)


class EncyclopediaCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="search_in_dune")
    @app_commands.describe(search_term="Type in the string you wish to search for.")
    async def search_in_dune(self, interaction: discord.Interaction, search_term: str):
        await interaction.response.defer()

        if len(search_term) < 3:
            await interaction.followup.send("Search term must be at least 3 characters long")
            return

        from media_fetcher import search_in_epub_with_element

        results = []

        results.append(search_in_epub_with_element(search_term, 1, 'p'))
        results.append(search_in_epub_with_element(search_term, 2, 'div'))
        results.append(search_in_epub_with_element(search_term, 3, 'p'))
        results.append(search_in_epub_with_element(search_term, 4, 'p'))
        results.append(search_in_epub_with_element(search_term, 5, 'p'))
        results.append(search_in_epub_with_element(search_term, 6, 'div'))

        results = [result for result in results if result is not None]

        from itertools import chain

        flattened_results = list(chain(*results))

        if len(results) == 0:
            await interaction.followup.send("No results found")
            return

        search_view = SearchResultView(flattened_results, search_term)

        await search_view.send(interaction)


async def setup(bot: commands.Bot) -> None: 
    await bot.add_cog(EncyclopediaCog(bot))