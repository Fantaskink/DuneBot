from PIL import Image
import requests
import numpy as np
from io import BytesIO

def get_primary_hex_color(image_url):
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))

    # Resize the image to a small size for faster processing (e.g., 100x100)
    #resized_image = image.resize((100, 100))
    
    # Convert the image to a NumPy array
    img_array = np.array(image)
    
    # Flatten the array to easily get color counts
    flat_array = img_array.reshape(-1, img_array.shape[-1])

    # Get the unique colors and their counts
    colors, counts = np.unique(flat_array, axis=0, return_counts=True)

    # Get the index of the most frequent color
    primary_color_index = np.argmax(counts)
    
    # Convert the RGB values to hex
    primary_color_rgb = colors[primary_color_index]
    primary_hex = '#{:02x}{:02x}{:02x}'.format(*primary_color_rgb)

    
    return int(primary_hex[1:], 16)