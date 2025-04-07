"""
Scraper for extracting data from a website
"""


import re
from typing import Any
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask_socketio import emit
import stealth_requests as requests
import time
import os

from tqdm import tqdm

load_dotenv(override=True)


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}
RATE_LIMIT = float(os.getenv("RATE_LIMIT"))  # seconds
TIME_OUT = float(os.getenv("TIME_OUT"))  # seconds
MAX_CONTEXT_SIZE = int(os.getenv("MAX_CONTEXT_SIZE"))  # maximum context size for the model
last_request_time = {}  # last request time for each domain

# print(f"Rate limit: {RATE_LIMIT} seconds")
# print(f"Timeout: {TIME_OUT} seconds")
# print(f"Max retries: {MAX_RETRIES}")
# print(f"Max context size: {MAX_CONTEXT_SIZE} tokens")

def rate_limit(url):
    """
    Rate limit the requests to avoid overwhelming the server.
    """
    domain = urlparse(url).netloc
    current_time = time.time()
    if domain in last_request_time:
        time_from_last_request = current_time - last_request_time[domain]
        if time_from_last_request < RATE_LIMIT:
            time.sleep(RATE_LIMIT - time_from_last_request)
    last_request_time[domain] = current_time


def scrape(url) -> dict[str, dict[str, Any] | str] | str:
    """
    Scrape the content from the given URL.
    Args:
        url (str): The URL to scrape.
    """
    try:
        rate_limit(url)

        # Fetch the content from the URL
        response = requests.get(url, headers=HEADERS, timeout=TIME_OUT, impersonate="safari")
        response.raise_for_status()  # Raise an error for bad responses

        # Parse the content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove unwanted tags
        for tag in soup(['nav', 'footer', 'aside', 'script', 'style']):
            tag.decompose()
            
        # Extract text from the soup object
        text = soup.get_text()
        
        text = re.sub(r'\s+', ' ', text).strip() # normalize whitespace
        text = re.sub(r'[^\w\s.,;:!?\'\"-]', '', text) # remove special characters
        
        # Truncate to fit context size
        text = " ".join(text.split()[:int(MAX_CONTEXT_SIZE / 8)]) # 1 token approximately 4 character
        
        links = {
            re.sub(r'\s+', ' ', a.text.strip()): a['href']
            for a in soup.find_all('a', href=True)[:int(MAX_CONTEXT_SIZE / 2000)] # tokens for links (link is short)
            if a.text.strip()
        }
        print(f"Scraped {len(links)} links from {url}")
        emit('receive_message', {'status': 'info',
             'message': "Scrape successful!"})
        
        return {"text": text, "links": links}
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        emit('receive_message',
                {'status': 'error', 'message': f"Error scraping {url}: {e}"})

def has_video_content(url):
    """
    Check if the URL contains video content.
    Args:
        url (str): The URL to check.
    """
    try:
        # Get the webpage content
        response = requests.get(url, verify=False, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check for common video elements
        video_elements = (
            soup.find_all('video') or
            soup.find_all('iframe', src=lambda x: x and ('youtube.com' in x or 'vimeo.com' in x)) or
            'youtube.com' in url or
            'vimeo.com' in url or
            any(vid_site in url for vid_site in [
                'dailymotion.com', 'twitter.com', 'tiktok.com',
                'facebook.com', 'instagram.com', 'reddit.com'
            ])
        )
        return bool(video_elements)
    except requests.RequestException as e:
        print(f"Error checking video content: {e}")
        return False
    
def download_file(url: str, output_path=None) -> str:
    """
    Download a file from the given URL.
    Args:
        url (str): The URL to download from.
    """
    try:
        response = requests.get(
            url=url, stream=True, verify=False, headers=HEADERS,timeout=TIME_OUT)
        # Check if the request was successful
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        output_path = output_path or os.path.join(
            os.getcwd(), os.path.basename(url))
        if os.path.isdir(output_path):
            output_path = os.path.join(output_path, os.path.basename(url))
        with open(output_path, 'wb') as file, tqdm(
            desc = f"Downloading {os.path.basename(url)}",
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
            initial=0
        ) as progress_bar:
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                progress_bar.update(size)
                
        print("File downloaded successfully at", output_path)
        return f"File downloaded successfully at {output_path}"
    except requests.exceptions.RequestException as e:
        print(f"Failed to download file: {e}")
        return f"Failed to download file: {e}"
    except IOError as e:
        print(f"Error while saving file: {e}")
        return f"Error while saving file: {e}"

# if __name__ == "__main__":
    # url = "https://www.vietcombank.com.vn/"
    # url = "https://www.vietcombank"
    # result = scrape(url)
    # print(result)