"""
Scraper for extracting data from a website
"""


import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests
import time
import os

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


def scrape(url):
    """
    Scrape the content from the given URL.
    Args:
        url (str): The URL to scrape.
    """
    try:
        rate_limit(url)

        # Fetch the content from the URL
        response = requests.get(url, headers=HEADERS, timeout=TIME_OUT)
        response.raise_for_status()  # Raise an error for bad responses

        # Parse the content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove unwanted tags
        for tag in soup(['nav', 'footer', 'aside', 'script', 'style']):
            tag.decompose()
            
        # Extract text from the soup object
        text = soup.get_text()
        
        text = re.sub(r'\s+', ' ', text).strip() # normalize whitespace
        text = re.sub(r'\n+', '\n', text).strip() # normalize newlines
        text = re.sub(r'\t+', '\t', text).strip() # normalize tabs
        text = re.sub(r'[^\w\s.,;:!?\'\"-]', '', text) # remove special characters
        text = re.sub(r'\s+', ' ', text).strip() # normalize whitespace
        
        # Truncate to fit context size
        text = " ".join(text.split()[:int(MAX_CONTEXT_SIZE / 8)]) # 1 token approximately 4 character
        
        links = {
            re.sub(r'\s+', ' ', a.text.strip()): a['href']
            for a in soup.find_all('a', href=True)[:int(MAX_CONTEXT_SIZE / 2000)] # tokens for links (link is short)
            if a.text.strip()
        }
        print(f"Scraped {len(links)} links from {url}")
        
        return {"text": text, "links": links}
    except Exception as e:
        print(f"Error scraping {url}: {e}")


if __name__ == "__main__":
    # url = "https://www.vietcombank.com.vn/"
    # url = "https://www.vietcombank"
    # result = scrape(url)
    # print(result)