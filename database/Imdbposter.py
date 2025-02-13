import re
import aiohttp
import asyncio
import logging
from io import BytesIO
from PIL import Image
from info import DEENDAYAL_IMAGE_FETCH
from imdb import Cinemagoer

# Initialize IMDb API client
ia = Cinemagoer()

# Enable logging
logger = logging.getLogger(__name__)

# Configuration: Whether to fetch long descriptions
LONG_IMDB_DESCRIPTION = False

def list_to_str(lst):
    """Converts a list to a comma-separated string, handling empty cases."""
    return ", ".join(map(str, lst)) if lst else "N/A"

async def fetch_image(url, size=(720, 720)):
    """Fetch and resize an image from a URL asynchronously."""
    if not DEENDAYAL_IMAGE_FETCH:
        logger.info("Image fetching is disabled.")
        return None

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    img = Image.open(BytesIO(content))

                    # Ensure it's a valid image format before proceeding
                    if img.format not in ["JPEG", "PNG", "WEBP"]:
                        logger.warning("Unsupported image format: %s", img.format)
                        return None
                    
                    img = img.resize(size, Image.LANCZOS)
                    img_byte_arr = BytesIO()
                    img.save(img_byte_arr, format='JPEG')
                    img_byte_arr.seek(0)
                    return img_byte_arr
                else:
                    logger.error(f"Failed to fetch image: HTTP {response.status}")
    except aiohttp.ClientError as e:
        logger.error(f"HTTP request error in fetch_image: {e}")
    except IOError as e:
        logger.error(f"IO error in fetch_image: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in fetch_image: {e}")
    
    return None
