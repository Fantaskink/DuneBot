import requests
from io import BytesIO
from colorthief import ColorThief

def get_primary_hex_color(image_url):
    response = requests.get(image_url)

    color_thief = ColorThief(BytesIO(response.content))

    dominant_color = color_thief.get_color(quality=1)

    # Convert the RGB values to hex
    primary_hex = '#{:02x}{:02x}{:02x}'.format(*dominant_color)
    
    return int(primary_hex[1:], 16)

#print(get_primary_hex_color('https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1602418924i/52729070.jpg'))