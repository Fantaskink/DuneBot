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




#print(search_in_epub_with_element("beefswelling", 3, "p"))